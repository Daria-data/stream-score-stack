"""Airflow DAG for the end-to-end data pipeline.

Orchestrates:
1) Multi-source extraction to ``data/staging``
2) Programmatic SQL extraction (PostgreSQL + DuckDB)
3) Normalize, clean, merge, and build the final dataset
4) Validate the final CSVs (row counts, NOT NULL on PKs/FKs)
5) Import CSVs into the normalized PostgreSQL target schema

Schedule:
    ``@daily`` with ``catchup=False``: runs once per day at midnight UTC.
    Can also be triggered manually from the Airflow UI.

Usage:
    - Open Airflow UI at http://localhost:8080
    - Trigger DAG ``e4_pipeline`` manually or wait for the daily run
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta

import pendulum
from airflow import DAG
from airflow.operators.python import PythonOperator

LOCAL_TZ = pendulum.timezone("UTC")

TASK_DEFAULTS: dict = {
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


def _configure_runtime_env() -> None:
    """Set environment variables required by project scripts.

    Airflow runs inside a dedicated container, so service hostnames and ports
    must point to Docker network names rather than localhost.
    """
    os.environ["DB_HOST"] = "postgres"
    os.environ["DB_PORT"] = "5432"
    os.environ["DB_NAME"] = "sports"
    os.environ["DB_USER"] = "postgres"
    os.environ["DB_PASSWORD"] = os.getenv("DB_PASSWORD", "postgres")
    os.environ["MOCK_API_URL"] = "http://mock-api:8000"


def run_extraction_step() -> None:
    """Run multi-source extraction and persist outputs to ``data/staging``."""
    _configure_runtime_env()
    from src.pipelines.extract.run_extraction import run_all

    run_all()


def run_sql_extraction_step() -> None:
    """Run documented SQL extraction queries for Postgres and DuckDB."""
    _configure_runtime_env()
    from src.pipelines.sql.run_sql_extraction import run_all

    run_all()


def run_aggregation_step() -> None:
    """Run normalization, cleaning, merge, and final dataset build."""
    _configure_runtime_env()
    from src.pipelines.transform.run_aggregation import run_full_pipeline

    run_full_pipeline()


def run_validate_step() -> None:
    """Check final CSVs before DB import: files exist, row counts, NOT NULL on key columns.

    Raises:
        FileNotFoundError: If a required CSV is missing.
        ValueError: If a CSV is empty or has NULL primary/foreign keys.
    """
    import logging
    from pathlib import Path

    import pandas as pd

    logger = logging.getLogger(__name__)
    final_dir = Path("/opt/airflow/data/final")
    if not final_dir.exists():
        final_dir = Path(__file__).resolve().parent.parent / "data" / "final"

    required_tables: dict[str, list[str]] = {
        "dim_country": ["id_country"],
        "dim_federation": ["id_federation"],
        "dim_sport": ["id_sport", "id_federation"],
        "dim_discipline": ["id_discipline"],
        "dim_epreuve": ["id_epreuve", "id_discipline", "id_sport"],
        "dim_edition": ["id_edition"],
        "dim_evenement": ["id_evenement", "id_epreuve", "id_edition"],
        "fact_result": ["id_result", "id_evenement", "id_country"],
    }

    for table, not_null_cols in required_tables.items():
        csv_path = final_dir / f"{table}.csv"
        if not csv_path.exists():
            raise FileNotFoundError(f"Missing: {csv_path}")
        df = pd.read_csv(csv_path, nrows=None)
        if df.empty:
            raise ValueError(f"{table}.csv is empty")
        for col in not_null_cols:
            if col not in df.columns:
                raise ValueError(
                    f"{table}.csv: required column '{col}' is missing from the file"
                )
            nulls = int(df[col].isna().sum())
            if nulls > 0:
                raise ValueError(
                    f"{table}.csv: {nulls} NULL values in required column '{col}'"
                )
        logger.info("OK  %-20s %d rows, NOT NULL checks passed", table, len(df))

    logger.info("All 8 final CSVs validated; safe to import.")


def run_import_step() -> None:
    """Load ``data/final`` CSVs into the normalized target schema."""
    _configure_runtime_env()
    from src.db.import_final_dataset import import_all

    import_all()


with DAG(
    dag_id="e4_pipeline",
    description="End-to-end pipeline: extract -> SQL -> aggregate -> validate -> import",
    start_date=datetime(2026, 1, 1, tzinfo=LOCAL_TZ),
    schedule="@daily",
    catchup=False,
    max_active_runs=1,
    default_args=TASK_DEFAULTS,
    tags=["e4", "pipeline"],
) as dag:
    extract_task = PythonOperator(
        task_id="extract_multi_sources",
        python_callable=run_extraction_step,
    )

    sql_extract_task = PythonOperator(
        task_id="sql_extraction",
        python_callable=run_sql_extraction_step,
    )

    aggregate_task = PythonOperator(
        task_id="aggregate_and_build_final",
        python_callable=run_aggregation_step,
    )

    validate_task = PythonOperator(
        task_id="validate_final_dataset",
        python_callable=run_validate_step,
    )

    import_task = PythonOperator(
        task_id="import_to_target_db",
        python_callable=run_import_step,
    )

    extract_task >> sql_extract_task >> aggregate_task >> validate_task >> import_task
