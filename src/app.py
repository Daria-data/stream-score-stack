"""
Mini-SQL playground for sports data.

Run locally:
    uv run streamlit run src/app.py

Environment variables expected:
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
"""

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine
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
    raw_conn = engine.raw_connection()           # psycopg2 connection
    try:
        return pd.read_sql_query(sql, raw_conn)  
    finally:
        raw_conn.close()

def get_last_update() -> datetime | None:
    """
    Query Airflow metadata to find the last successful execution_date
    for the ingest_every_2_years DAG.
    """
    sql = (
        "SELECT MAX(execution_date) AS last_update "
        "FROM dag_run "
        "WHERE dag_id = 'ingest_every_2_years';"
    )
    df = execute_sql(sql)
    if df.empty or pd.isna(df.at[0, "last_update"]):
        return None
    return pd.to_datetime(df.at[0, "last_update"])

def fetch_columns(table: str) -> list[str]:
    """Return a list of column names for the given table."""
    sql = (
        "SELECT column_name "
        "FROM information_schema.columns "
        f"WHERE table_name = '{table}' "
        "ORDER BY ordinal_position;"
    )
    df = execute_sql(sql)
    return df["column_name"].tolist()

def main() -> None:
    """Streamlit UI definition."""
    st.set_page_config(
        page_title="Olympic Results - SQL Playground",
        layout="wide",
    )
    TABLE = "jo"
    # Sidebar
    st.sidebar.title("📊 Table Info")
    st.sidebar.markdown(f"**Table name:** `{TABLE}`")
    st.sidebar.markdown(
        "**Description:** Results of all events from Winter and Summer Olympic Games"
    )
    # show last update in sidebar
    last = get_last_update()
    if last is not None:
        st.sidebar.info(f"Last refresh: {last.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        st.sidebar.warning("Data not ingested yet.")
    columns = fetch_columns(TABLE)
    sel_cols = st.sidebar.multiselect(
        "Select here columns to display", columns, default=columns[:3]
    )

    st.sidebar.markdown("---")
    st.sidebar.title("⚡ Quick Templates")

    templates: dict[str, str] = {
        "Show head": f"SELECT * FROM {TABLE} LIMIT 10;",
        "Medal tally by country - 2024": f"""
SELECT
  pays_en_base_resultats AS country,
  SUM(CASE WHEN classement_epreuve = '1' THEN 1 ELSE 0 END) AS gold_count,
  SUM(CASE WHEN classement_epreuve = '2' THEN 1 ELSE 0 END) AS silver_count,
  SUM(CASE WHEN classement_epreuve = '3' THEN 1 ELSE 0 END) AS bronze_count,
  COUNT(*) FILTER (WHERE classement_epreuve IN ('1','2','3')) AS total_medals
FROM {TABLE}
WHERE edition_saison = '2024'
  AND pays_en_base_resultats <> ''
GROUP BY country
ORDER BY gold_count DESC;
""",
        "Athlete medal tally": f"""
SELECT
  athlete_prenom || ' ' || athlete_nom      AS athlete,
  sport_en                                 AS sport,
  pays_en_base_resultats                   AS country,
  edition_saison                           AS year,
  SUM(CASE WHEN classement_epreuve = '1' THEN 1 ELSE 0 END) AS gold_count,
  SUM(CASE WHEN classement_epreuve = '2' THEN 1 ELSE 0 END) AS silver_count,
  SUM(CASE WHEN classement_epreuve = '3' THEN 1 ELSE 0 END) AS bronze_count,
  COUNT(*) FILTER (WHERE classement_epreuve IN ('1','2','3'))   AS total_medals
FROM {TABLE}
WHERE
  pays_en_base_resultats <> ''
  AND athlete_prenom NOT IN ('', 'NULL')
  AND athlete_nom    NOT IN ('', 'NULL')
GROUP BY
  athlete_prenom || ' ' || athlete_nom,
  sport_en,
  pays_en_base_resultats,
  edition_saison
ORDER BY gold_count DESC;
""",
    }

    # Initialize SQL query in session state
    if 'sql_query' not in st.session_state:
        st.session_state['sql_query'] = templates['Show head']

    # Template buttons
    for label, sql in templates.items():
        if st.sidebar.button(label):
            st.session_state['sql_query'] = sql

    st.title("Olympic Results - SQL Playground")
    st.markdown("⚡ Use the sidebar templates or column selector to build your query" )
    sql_query = st.text_area(
        "SQL query",
        value=st.session_state['sql_query'],
        height=150,
        key='sql_editor'
    )
    st.session_state['sql_query'] = sql_query
    run_btn = st.button("Run query", type="primary")

    if run_btn and sql_query.strip():
        try:
            df = execute_sql(sql_query)
            st.dataframe(df)
            st.success(f"Returned {len(df)} rows.")
            # Export buttons
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="results.csv",
                mime="text/csv"
            )
            towrite = BytesIO()
            df.to_excel(towrite, index=False, sheet_name='Sheet1')
            towrite.seek(0)
            st.download_button(
                label="Download Excel",
                data=towrite,
                file_name="results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except SQLAlchemyError as exc:
            st.error(f"SQL error: {exc}")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Unexpected error: {exc}")

if __name__ == "__main__":
    main()
