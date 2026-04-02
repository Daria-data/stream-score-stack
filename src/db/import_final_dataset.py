"""Import the final aggregated dataset into the normalized target schema.

Covers C11 requirement: creating and populating the target database.
Reads CSV files from data/final/ and loads them into PostgreSQL
in FK-safe order (dimensions first, then fact table).

Usage:
    uv run python src/db/import_final_dataset.py

Environment variables:
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
"""

from __future__ import annotations

import io
import logging
import os
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent.parent
FINAL_DIR = ROOT / "data" / "final"
DDL_PATH = ROOT / "sql" / "init_target_db.sql"

# FK-safe loading order: parent dimensions before children, fact last.
LOAD_ORDER: list[str] = [
    "dim_country",
    "dim_federation",
    "dim_sport",
    "dim_discipline",
    "dim_epreuve",
    "dim_edition",
    "dim_evenement",
    "fact_result",
]


def _get_engine() -> Engine:
    """Build SQLAlchemy engine from environment variables.

    Returns:
        Configured Engine instance.
    """
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5433")
    name = os.getenv("DB_NAME", "sports")
    user = os.getenv("DB_USER", "postgres")
    pwd = os.getenv("DB_PASSWORD", "postgres")
    url = f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{name}"
    return create_engine(url, pool_pre_ping=True)


def create_target_schema(engine: Engine) -> None:
    """Execute the DDL script to create target tables.

    Args:
        engine: SQLAlchemy engine.
    """
    ddl = DDL_PATH.read_text(encoding="utf-8")
    with engine.begin() as conn:
        conn.execute(text(ddl))
    logger.info("Target schema created (or already exists)")


def truncate_tables(engine: Engine) -> None:
    """Truncate all target tables in reverse order to respect FK constraints.

    Args:
        engine: SQLAlchemy engine.
    """
    with engine.begin() as conn:
        for table in reversed(LOAD_ORDER):
            conn.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
    logger.info("All target tables truncated")


def load_csv_via_copy(engine: Engine, table: str, csv_path: Path) -> int:
    """Load a CSV file into a table using PostgreSQL COPY for efficiency.

    Args:
        engine: SQLAlchemy engine.
        table: Target table name.
        csv_path: Path to the CSV file.

    Returns:
        Number of rows loaded.
    """
    df = pd.read_csv(csv_path, encoding="utf-8")

    if df.empty:
        logger.warning("  %s: CSV is empty, skipping", table)
        return 0

    # Fix pandas float-promotion for nullable integer columns.
    int_cols = [
        "id_country", "id_federation", "id_sport", "id_discipline",
        "id_epreuve", "id_edition", "id_evenement", "id_result",
        "id_athlete", "id_team", "rank", "result_direction", "season_year",
    ]
    for col in int_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    columns = list(df.columns)
    col_list = ", ".join(columns)

    buf = io.StringIO()
    df.to_csv(buf, index=False, header=False, na_rep="\\N")
    buf.seek(0)

    raw_conn = engine.raw_connection()
    try:
        with raw_conn.cursor() as cur:
            cur.copy_expert(
                f"COPY {table} ({col_list}) FROM STDIN WITH (FORMAT csv, NULL '\\N')",
                buf,
            )
        raw_conn.commit()
    finally:
        raw_conn.close()

    return len(df)


def import_all() -> None:
    """Execute full import pipeline: create schema, truncate, load all tables."""
    engine = _get_engine()

    print("\n" + "=" * 65)
    print("DATABASE IMPORT — Loading Final Dataset into Target Schema (C11)")
    print("=" * 65)

    # Step 1: ensure target tables exist
    print("\n[Step 1] Creating target schema...")
    create_target_schema(engine)

    # Step 2: truncate existing data
    print("[Step 2] Truncating existing data...")
    truncate_tables(engine)

    # Step 3: load CSVs in FK-safe order
    print("[Step 3] Loading CSV files...\n")
    total_rows = 0
    results: list[tuple[str, int, str]] = []

    for table in LOAD_ORDER:
        csv_path = FINAL_DIR / f"{table}.csv"
        if not csv_path.exists():
            logger.warning("  %s: file not found at %s", table, csv_path)
            results.append((table, 0, "MISSING"))
            continue

        try:
            rows = load_csv_via_copy(engine, table, csv_path)
            total_rows += rows
            results.append((table, rows, "OK"))
            print(f"  {table:<20} {rows:>8} rows  OK")
        except Exception as exc:
            logger.error("  %s: FAILED — %s", table, exc)
            results.append((table, 0, f"FAIL: {exc}"))
            print(f"  {table:<20} {'0':>8} rows  FAIL: {exc}")

    # Step 4: verify with row counts
    print(f"\n[Step 4] Verifying row counts...")
    with engine.connect() as conn:
        for table in LOAD_ORDER:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"  {table:<20} {count:>8} rows in DB")

    # Summary
    print("\n" + "-" * 65)
    ok = sum(1 for _, _, s in results if s == "OK")
    fail = len(results) - ok
    print(f"Total: {ok} tables loaded, {fail} failed/missing, {total_rows} rows")
    print("=" * 65 + "\n")

    engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    import_all()
