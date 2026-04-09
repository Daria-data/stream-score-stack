"""Olympic Results: SQL Playground (normalized schema).

Interactive Streamlit app to query the normalized Olympic results database
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

# SQL bodies without banner line (banner added in TEMPLATES for editor + result title).
_RAW_TEMPLATES: dict[str, str] = {
    # Analytical queries (target schema)
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
    "Top athletes by medal count": """
SELECT r.athlete_first_name || ' ' || r.athlete_last_name AS athlete,
       c.country_name,
       COUNT(*) AS medal_count
FROM fact_result r
JOIN dim_country c ON r.id_country = c.id_country
WHERE r.athlete_last_name IS NOT NULL
  AND r.athlete_last_name <> ''
  AND r.rank IS NOT NULL
  AND r.rank IN (1, 2, 3)
GROUP BY athlete, c.country_name
ORDER BY medal_count DESC
LIMIT 20;
""",
    # Queries on legacy PostgreSQL schema `source` (not normalized dim_*)
    "Épreuves par discipline (schéma source)": """
SELECT id_discipline_administrative,
       discipline_administrative,
       COUNT(*) AS epreuve_count
FROM source.epreuves
GROUP BY id_discipline_administrative, discipline_administrative
ORDER BY epreuve_count DESC;
""",
    "Épreuves olympiques d'été (schéma source)": """
SELECT id_epreuve,
       epreuve,
       epreuve_genre,
       discipline_administrative
FROM source.epreuves
WHERE est_epreuve_olympique = 1
  AND est_epreuve_ete = 1
ORDER BY discipline_administrative, epreuve;
""",
    "Événements par édition (schéma source)": """
SELECT e.season_year,
       e.city,
       e.competition_type,
       COUNT(*) AS event_count
FROM source.evenements ev
JOIN dim_edition e ON ev.id_edition = e.id_edition
GROUP BY e.season_year, e.city, e.competition_type
ORDER BY e.season_year DESC;
""",
    "Audit source: événements sans épreuve liée (FK / qualité)": """
SELECT ev.id_evenement,
       ev.evenement,
       ev.id_epreuve
FROM source.evenements ev
LEFT JOIN source.epreuves ep ON ev.id_epreuve = ep.id_epreuve
WHERE ep.id_epreuve IS NULL;
""",
    # Target schema integrity checks (post-load validation)
    "Audit cible: id_sport NULL sur dim_epreuve (contrainte NOT NULL)": """
SELECT count(*) AS orphans
FROM   dim_epreuve
WHERE  id_sport IS NULL;
""",
    "Audit cible: id_sport sans ligne dim_sport (FK / orphelins)": """
SELECT e.id_epreuve, e.id_sport
FROM   dim_epreuve e
LEFT JOIN dim_sport s ON s.id_sport = e.id_sport
WHERE  s.id_sport IS NULL;
""",
    # Browse dimension and fact tables
    "Browse dim_country": "SELECT * FROM dim_country ORDER BY country_name LIMIT 50;",
    "Browse dim_federation": "SELECT * FROM dim_federation ORDER BY federation_name LIMIT 50;",
    "Browse dim_sport": """
SELECT s.id_sport, s.sport_name_fr, s.sport_name_en,
       f.federation_name
FROM dim_sport s
LEFT JOIN dim_federation f ON s.id_federation = f.id_federation
ORDER BY s.sport_name_fr LIMIT 50;
""",
    "Browse dim_discipline": "SELECT * FROM dim_discipline ORDER BY discipline_name LIMIT 50;",
    "Browse dim_epreuve": """
SELECT id_epreuve, epreuve_name, genre, epreuve_type,
       id_discipline, id_sport
FROM dim_epreuve
ORDER BY epreuve_name LIMIT 50;
""",
    "Browse dim_edition": "SELECT * FROM dim_edition ORDER BY season_year DESC;",
    "Browse dim_evenement": """
SELECT id_evenement, event_name_fr, event_name_en,
       id_epreuve, id_edition
FROM dim_evenement
ORDER BY id_evenement
LIMIT 50;
""",
    "Browse fact_result": "SELECT * FROM fact_result ORDER BY id_result LIMIT 50;",
}


def _template_sql_with_banner(label: str, sql_body: str) -> str:
    """Prefix SQL with a comment so the active template name is visible in the editor.

    Args:
        label: Sidebar button label (template name).
        sql_body: Raw SQL without the banner line.

    Returns:
        SQL string with a leading ``-- Template:`` comment.
    """
    cleaned = sql_body.strip()
    return f"-- Template: {label}\n{cleaned}\n"


def _extract_template_title(sql: str) -> str | None:
    """Return the template title from the first ``-- Template:`` line, if any.

    Args:
        sql: Full query text from the editor.

    Returns:
        The title after ``-- Template:``, or None for ad-hoc SQL.
    """
    for raw in sql.strip().splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("-- Template:"):
            return line.removeprefix("-- Template:").strip()
        if not line.startswith("--"):
            break
    return None


TEMPLATES: dict[str, str] = {
    label: _template_sql_with_banner(label, body)
    for label, body in _RAW_TEMPLATES.items()
}


def main() -> None:
    """Streamlit UI definition."""
    st.set_page_config(
        page_title="Olympic Results: SQL Playground",
        layout="wide",
    )

    # Left-align Quick Templates button labels (default Streamlit centers short labels).
    st.markdown(
        """
        <style>
        section[data-testid="stSidebar"] div.stButton > button {
            justify-content: flex-start;
            text-align: left;
        }
        section[data-testid="stSidebar"] div.stButton > button p {
            text-align: left;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Sidebar
    st.sidebar.title("Olympic Results DB")

    st.sidebar.markdown("### Schema overview")
    counts = get_table_counts()
    schema_md = "| Table | Rows |\n|:------|-----:|\n"
    for table, count in counts.items():
        schema_md += f"| `{table}` | **{count:,}** |\n"
    st.sidebar.markdown(schema_md, unsafe_allow_html=True)

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

    # Main area
    st.title("Olympic Results: SQL Playground")
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
            template_title = _extract_template_title(sql_query)
            if template_title:
                st.subheader(f"Results: {template_title}")
            else:
                st.caption("Custom SQL (no template banner)")

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
