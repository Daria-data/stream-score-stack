from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import pendulum
import pandas as pd
from airflow import DAG
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.operators.python import PythonOperator

LOCAL_TZ = pendulum.timezone("UTC")
CSV_PATH = "/csv/fact_resultats_epreuves.csv"        
TABLE = "jo"
DATE_COL = "date_debut_edition"

def upsert_new_rows() -> None:
    """
    1. Query the max DATE_COL already in TABLE.
    2. Read the CSV, parse DATE_COL to datetime.
    3. Filter rows with DATE_COL > max_date.
    4. Insert those rows into TABLE as new batch.
    """
    hook = PostgresHook(postgres_conn_id="sports_db")
    conn = hook.get_conn()
    with conn.cursor() as cur:
        cur.execute(
            f'SELECT COALESCE(MAX("{DATE_COL}"), DATE \'1900-01-01\') '
            f'FROM "{TABLE}";'
        )
        last_date = cur.fetchone()[0]

    # read all as strings, then convert DATE_COL
    df = pd.read_csv(CSV_PATH, dtype=str)
    df[DATE_COL] = pd.to_datetime(df[DATE_COL], errors="coerce")

    # keep only rows strictly newer than last_date
    new_rows = df[df[DATE_COL] > pd.to_datetime(last_date)]

    if not new_rows.empty:
        # insert_rows expects list of tuples/rows
        hook.insert_rows(TABLE, new_rows.astype(str).values.tolist())


with DAG(
    dag_id="ingest_every_2_years",
    start_date=datetime(2025, 1, 1, tzinfo=LOCAL_TZ),
    catchup=False,
    schedule_interval=relativedelta(years=2), 
    max_active_runs=1,
    tags=["ingest"],
) as dag:
    PythonOperator(
        task_id="upsert_new_rows",
        python_callable=upsert_new_rows,
    )
