"""Airflow DAG for the end-to-end E4 data pipeline.

This DAG orchestrates all core project steps:
1) Multi-source extraction (C8)
2) Programmatic SQL extraction (C9)
3) Aggregation and cleaning (C10)
4) Import into normalized target database (C11)

Usage:
    - Open Airflow UI at http://localhost:8080
    - Trigger DAG `e4_pipeline` manually
"""

from __future__ import annotations

import os
from datetime import datetime

import pendulum
from airflow import DAG
from airflow.operators.python import PythonOperator

LOCAL_TZ = pendulum.timezone("UTC")


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
    """Run C8 extraction pipeline and persist outputs to data/staging."""
    _configure_runtime_env()
    from src.pipelines.extract.run_extraction import run_all

    run_all()


def run_sql_extraction_step() -> None:
    """Run C9 SQL extraction queries for Postgres and DuckDB."""
    _configure_runtime_env()
    from src.pipelines.sql.run_sql_extraction import run_all

    run_all()


def run_aggregation_step() -> None:
    """Run C10 normalization, cleaning, merge, and final dataset build."""
    _configure_runtime_env()
    from src.pipelines.transform.run_aggregation import run_full_pipeline

    run_full_pipeline()


def run_import_step() -> None:
    """Run C11 import into the normalized target schema tables."""
    _configure_runtime_env()
    from src.db.import_final_dataset import import_all

    import_all()


with DAG(
    dag_id="e4_pipeline",
    description="E4 end-to-end data pipeline: extract -> SQL -> aggregate -> import",
    start_date=datetime(2026, 1, 1, tzinfo=LOCAL_TZ),
    schedule_interval=None,
    catchup=False,
    max_active_runs=1,
    tags=["e4", "pipeline", "c8", "c9", "c10", "c11"],
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

    import_task = PythonOperator(
        task_id="import_to_target_db",
        python_callable=run_import_step,
    )

    extract_task >> sql_extract_task >> aggregate_task >> import_task
