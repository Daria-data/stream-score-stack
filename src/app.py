"""Olympic Results — SQL Playground (normalized schema).

Interactive Streamlit app to query the E4 normalized database
(dim_* dimension tables + fact_result fact table).

Run locally:
    uv run streamlit run src/app.py

Environment variables:
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
"""

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from config import settings
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from io import BytesIO


@st.cache_resource(show_spinner=False)
def get_engine() -> Engine:
    """Create a SQLAlchemy engine using ENV variables."""
    db_url = (
        f"postgresql+psycopg2://{settings.db_user}:{settings.db_password}"
        f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
    )
    return create_engine(db_url, pool_pre_ping=True)


def execute_sql(sql: str) -> pd.DataFrame:
    """Run raw SQL and return result as DataFrame."""
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        return pd.DataFrame(result.fetchall(), columns=result.keys())


def get_table_counts() -> dict[str, int]:
    """Fetch row counts for all target schema tables."""
    tables = [
        "dim_country", "dim_federation", "dim_sport", "dim_discipline",
        "dim_epreuve", "dim_edition", "dim_evenement", "fact_result",
    ]
    counts: dict[str, int] = {}
    for t in tables:
        try:
            df = execute_sql(f"SELECT COUNT(*) AS cnt FROM {t}")
            counts[t] = int(df.at[0, "cnt"])
        except Exception:
            counts[t] = 0
    return counts


def get_last_pipeline_run() -> datetime | None:
    """Query Airflow metadata for the last successful e4_pipeline run."""
    sql = (
        "SELECT MAX(execution_date) AS last_update "
        "FROM dag_run "
        "WHERE dag_id = 'e4_pipeline' "
        "AND state = 'success';"
    )
    try:
        df = execute_sql(sql)
        if df.empty or pd.isna(df.at[0, "last_update"]):
            return None
        return pd.to_datetime(df.at[0, "last_update"])
    except Exception:
        return None


TABLES = [
    "dim_country", "dim_federation", "dim_sport", "dim_discipline",
    "dim_epreuve", "dim_edition", "dim_evenement", "fact_result",
]

TEMPLATES: dict[str, str] = {
    # ── Analytical queries (target schema) ──
    "Top 10 countries by results": """
SELECT c.country_name,
       COUNT(*) AS total_results
FROM fact_result r
JOIN dim_country c ON r.id_country = c.id_country
GROUP BY c.country_name
ORDER BY total_results DESC
LIMIT 10;
""",
    "Results by edition (year / city)": """
SELECT e.season_year,
       e.city,
       e.competition_type,
       COUNT(*) AS results
FROM fact_result r
JOIN dim_evenement ev ON r.id_evenement = ev.id_evenement
JOIN dim_edition e ON ev.id_edition = e.id_edition
GROUP BY e.season_year, e.city, e.competition_type
ORDER BY e.season_year DESC;
""",
    "Sports list with federations": """
SELECT f.federation_name,
       s.sport_name_fr,
       s.sport_name_en
FROM dim_sport s
LEFT JOIN dim_federation f ON s.id_federation = f.id_federation
ORDER BY f.federation_name;
""",
    "Top athletes (individual results)": """
SELECT r.athlete_first_name || ' ' || r.athlete_last_name AS athlete,
       c.country_name,
       COUNT(*) AS participations
FROM fact_result r
JOIN dim_country c ON r.id_country = c.id_country
WHERE r.athlete_last_name IS NOT NULL
  AND r.athlete_last_name <> ''
GROUP BY athlete, c.country_name
ORDER BY participations DESC
LIMIT 20;
""",
    # ── C9 documented queries (source schema) ──
    "C9: Épreuves per discipline (source)": """
SELECT id_discipline_administrative,
       discipline_administrative,
       COUNT(*) AS epreuve_count
FROM source.epreuves
GROUP BY id_discipline_administrative, discipline_administrative
ORDER BY epreuve_count DESC;
""",
    "C9: Olympic summer events only (source)": """
SELECT id_epreuve,
       epreuve,
       epreuve_genre,
       discipline_administrative
FROM source.epreuves
WHERE est_epreuve_olympique = 1
  AND est_epreuve_ete = 1
ORDER BY discipline_administrative, epreuve;
""",
    "C9: Événements per edition (source)": """
SELECT e.season_year,
       e.city,
       e.competition_type,
       COUNT(*) AS event_count
FROM source.evenements ev
JOIN dim_edition e ON ev.id_edition = e.id_edition
GROUP BY e.season_year, e.city, e.competition_type
ORDER BY event_count DESC;
""",
    "C9: Orphan événements — no épreuve (source)": """
SELECT ev.id_evenement,
       ev.evenement,
       ev.id_epreuve
FROM source.evenements ev
LEFT JOIN source.epreuves ep ON ev.id_epreuve = ep.id_epreuve
WHERE ep.id_epreuve IS NULL;
""",
    # ── Browse tables ──
    "Browse dim_country": "SELECT * FROM dim_country ORDER BY country_name LIMIT 50;",
    "Browse dim_edition": "SELECT * FROM dim_edition ORDER BY season_year DESC LIMIT 50;",
    "Browse dim_epreuve": "SELECT * FROM dim_epreuve LIMIT 50;",
    "Browse fact_result (first 50)": "SELECT * FROM fact_result LIMIT 50;",
}


def main() -> None:
    """Streamlit UI definition."""
    st.set_page_config(
        page_title="Olympic Results — SQL Playground",
        layout="wide",
    )

    # ── Sidebar ──────────────────────────────────────────────
    st.sidebar.title("Olympic Results DB")

    st.sidebar.markdown("### Schema overview")
    counts = get_table_counts()
    for table, count in counts.items():
        label = table.replace("dim_", "").replace("fact_", "")
        st.sidebar.metric(label=table, value=f"{count:,} rows")

    st.sidebar.markdown("---")

    last = get_last_pipeline_run()
    if last is not None:
        st.sidebar.success(f"Last pipeline run: {last.strftime('%Y-%m-%d %H:%M')}")
    else:
        st.sidebar.info("Pipeline not yet run via Airflow (data loaded by loader).")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Quick Templates")

    if "sql_query" not in st.session_state:
        st.session_state["sql_query"] = TEMPLATES["Top 10 countries by results"]

    for label, sql in TEMPLATES.items():
        if st.sidebar.button(label):
            st.session_state["sql_query"] = sql

    # ── Main area ────────────────────────────────────────────
    st.title("Olympic Results — SQL Playground")
    st.caption(
        "Query the normalized database: 7 dimension tables + 1 fact table. "
        "Use sidebar templates or write custom SQL."
    )

    sql_query = st.text_area(
        "SQL query",
        value=st.session_state["sql_query"],
        height=160,
        key="sql_editor",
    )
    st.session_state["sql_query"] = sql_query

    run_btn = st.button("Run query", type="primary")

    if run_btn and sql_query.strip():
        try:
            df = execute_sql(sql_query)
            st.dataframe(df, use_container_width=True)
            st.success(f"Returned {len(df)} rows.")

            col1, col2 = st.columns(2)
            with col1:
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name="results.csv",
                    mime="text/csv",
                )
            with col2:
                buf = BytesIO()
                df.to_excel(buf, index=False, sheet_name="Sheet1")
                buf.seek(0)
                st.download_button(
                    label="Download Excel",
                    data=buf,
                    file_name="results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
        except SQLAlchemyError as exc:
            st.error(f"SQL error: {exc}")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Unexpected error: {exc}")


if __name__ == "__main__":
    main()
