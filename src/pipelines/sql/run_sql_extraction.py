"""Execute documented SQL extraction queries programmatically.

Reads SQL files, parses named queries, runs them against PostgreSQL and DuckDB,
and writes results to staging.

Usage:
    uv run python -m src.pipelines.sql.run_sql_extraction

Environment variables:
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD (for Postgres)
"""

from __future__ import annotations

import logging
import os
import re
import time
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent.parent.parent
SQL_DIR = ROOT / "sql" / "extraction"
STAGING_DIR = ROOT / "data" / "staging"
SQL_STAGING_DIR = STAGING_DIR / "sql"
PARQUET_PATH = ROOT / "data" / "parquet" / "athletes_teams.parquet"


def _get_pg_engine() -> Engine:
    """Build SQLAlchemy engine for PostgreSQL.

    Returns:
        Configured Engine instance.
    """
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5433")
    name = os.getenv("DB_NAME", "sports")
    user = os.getenv("DB_USER", "postgres")
    pwd = os.getenv("DB_PASSWORD", "postgres")
    url = f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{name}"
    return create_engine(url)


def parse_sql_file(sql_path: Path) -> list[dict[str, str]]:
    """Parse a SQL file into named query blocks.

    Expects format:
        -- QUERY N: Title
        -- ... documentation ...
        SELECT ...;

    Args:
        sql_path: Path to the SQL file.

    Returns:
        List of dicts with keys: name, title, sql, docs.
    """
    content = sql_path.read_text(encoding="utf-8")
    
    # Pattern to split by query headers
    pattern = r"--\s*-+\s*\n--\s*QUERY\s+(\d+):\s*(.+?)\n(.*?)(?=--\s*-+\s*\n--\s*QUERY|\Z)"
    matches = re.findall(pattern, content, re.DOTALL)
    
    queries: list[dict[str, str]] = []
    for num, title, block in matches:
        # Extract documentation (comment lines) and SQL
        lines = block.strip().split("\n")
        doc_lines: list[str] = []
        sql_lines: list[str] = []
        in_sql = False
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("--"):
                if not in_sql:
                    doc_lines.append(stripped[2:].strip())
            elif stripped:
                in_sql = True
                sql_lines.append(line)
            elif in_sql:
                sql_lines.append(line)
        
        sql_text = "\n".join(sql_lines).strip().rstrip(";")
        
        queries.append({
            "name": f"query_{num}",
            "title": title.strip(),
            "docs": " ".join(doc_lines),
            "sql": sql_text,
        })
    
    return queries


def run_postgres_queries() -> list[dict[str, Any]]:
    """Execute all queries from postgres_extract.sql.

    Returns:
        List of execution results with metadata.
    """
    sql_file = SQL_DIR / "postgres_extract.sql"
    if not sql_file.exists():
        logger.warning("postgres_extract.sql not found")
        return []
    
    queries = parse_sql_file(sql_file)
    engine = _get_pg_engine()
    results: list[dict[str, Any]] = []

    try:
        # Validate DB connectivity once before running all queries.
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        with engine.connect() as conn:
            for q in queries:
                logger.info("Executing PG %s: %s", q["name"], q["title"])
                t0 = time.time()
                try:
                    result_proxy = conn.execute(text(q["sql"]))
                    df = pd.DataFrame(result_proxy.fetchall(), columns=result_proxy.keys())
                    elapsed = round(time.time() - t0, 2)

                    out_path = SQL_STAGING_DIR / f"sql_pg_{q['name']}.csv"
                    df.to_csv(out_path, index=False, encoding="utf-8")

                    results.append({
                        "source": "postgres",
                        "name": q["name"],
                        "title": q["title"],
                        "rows": len(df),
                        "file": out_path.name,
                        "seconds": elapsed,
                        "status": "OK",
                    })
                    logger.info("  OK: %d rows, saved to %s", len(df), out_path.name)
                except Exception as exc:
                    logger.error("  FAILED: %s", exc)
                    results.append({
                        "source": "postgres",
                        "name": q["name"],
                        "title": q["title"],
                        "rows": 0,
                        "file": "-",
                        "seconds": 0,
                        "status": f"FAIL: {exc}",
                    })
    except OperationalError as exc:
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "5433")
        logger.warning("Postgres not reachable at %s:%s, skipping PG queries: %s", host, port, exc)
        for q in queries:
            results.append({
                "source": "postgres",
                "name": q["name"],
                "title": q["title"],
                "rows": 0,
                "file": "-",
                "seconds": 0,
                "status": "SKIPPED: Postgres not reachable",
            })
    finally:
        engine.dispose()

    return results


def run_duckdb_queries() -> list[dict[str, Any]]:
    """Execute all queries from duckdb_extract.sql.

    Returns:
        List of execution results with metadata.
    """
    sql_file = SQL_DIR / "duckdb_extract.sql"
    if not sql_file.exists():
        logger.warning("duckdb_extract.sql not found")
        return []
    
    if not PARQUET_PATH.exists():
        logger.warning("Parquet file not found: %s", PARQUET_PATH)
        return []
    
    queries = parse_sql_file(sql_file)
    parquet_str = str(PARQUET_PATH).replace("\\", "/")
    results: list[dict[str, Any]] = []
    
    conn = duckdb.connect()
    
    for q in queries:
        logger.info("Executing DuckDB %s: %s", q["name"], q["title"])
        t0 = time.time()
        try:
            # Replace placeholder with actual path
            sql = q["sql"].replace("{PARQUET_PATH}", parquet_str)
            df = conn.execute(sql).df()
            elapsed = round(time.time() - t0, 2)
            
            out_path = SQL_STAGING_DIR / f"sql_duckdb_{q['name']}.csv"
            df.to_csv(out_path, index=False, encoding="utf-8")
            
            results.append({
                "source": "duckdb",
                "name": q["name"],
                "title": q["title"],
                "rows": len(df),
                "file": out_path.name,
                "seconds": elapsed,
                "status": "OK",
            })
            logger.info("  OK: %d rows, saved to %s", len(df), out_path.name)
        except Exception as exc:
            logger.error("  FAILED: %s", exc)
            results.append({
                "source": "duckdb",
                "name": q["name"],
                "title": q["title"],
                "rows": 0,
                "file": "-",
                "seconds": 0,
                "status": f"FAIL: {exc}",
            })
    
    conn.close()
    return results


def run_all() -> None:
    """Execute all SQL extraction queries and print summary."""
    SQL_STAGING_DIR.mkdir(parents=True, exist_ok=True)
    all_results: list[dict[str, Any]] = []
    
    print("\n" + "=" * 75)
    print("SQL EXTRACTION: Programmatic query execution")
    print("=" * 75)
    
    # Postgres queries
    print("\n[PostgreSQL Queries]")
    pg_results = run_postgres_queries()
    all_results.extend(pg_results)
    
    # DuckDB queries
    print("\n[DuckDB / Parquet Queries]")
    duck_results = run_duckdb_queries()
    all_results.extend(duck_results)
    
    # Summary
    print("\n" + "-" * 75)
    print(f"{'SOURCE':<10} {'QUERY':<12} {'TITLE':<35} {'ROWS':>8} {'STATUS'}")
    print("-" * 75)
    for r in all_results:
        title_short = r["title"][:33] + ".." if len(r["title"]) > 35 else r["title"]
        print(f"{r['source']:<10} {r['name']:<12} {title_short:<35} {r['rows']:>8} {r['status']}")
    print("-" * 75)
    
    ok = sum(1 for r in all_results if r["status"] == "OK")
    skipped = sum(1 for r in all_results if str(r["status"]).startswith("SKIPPED"))
    fail = len(all_results) - ok - skipped
    print(f"Total: {ok} OK, {skipped} SKIPPED, {fail} FAILED")
    print(f"Output: {SQL_STAGING_DIR}\n")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    run_all()
