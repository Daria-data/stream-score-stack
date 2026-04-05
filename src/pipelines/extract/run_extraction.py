"""Orchestrate all 5 extraction steps sequentially.

Runs each extractor, logs success/failure per step,
and prints a final summary.

Usage:
    uv run python -m src.pipelines.extract.run_extraction

Environment variables (for Postgres extractor):
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
    MOCK_API_URL  (default: http://localhost:8000)
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path

logger = logging.getLogger(__name__)

STAGING_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "staging"


def run_all() -> None:
    """Execute every extraction step and report results.

    Each step is wrapped in try/except so that a single failure
    does not block the remaining extractors.
    """
    results: list[dict[str, str | int | float]] = []
    total_start = time.time()

    # ── Step 1: REST API ────────────────────────────────────────
    try:
        from src.pipelines.extract.extract_from_api import run as run_api

        base_url = os.getenv("MOCK_API_URL", "http://localhost:8000")
        t0 = time.time()
        outputs = run_api(base_url)
        elapsed = time.time() - t0
        for name, path in outputs.items():
            results.append({"step": "API", "dataset": name, "file": path.name,
                            "status": "OK", "seconds": round(elapsed, 2)})
    except Exception as exc:
        logger.error("API extraction failed: %s", exc)
        results.append({"step": "API", "dataset": "-", "file": "-",
                        "status": f"FAIL: {exc}", "seconds": 0})

    # ── Step 2: CSV file ────────────────────────────────────────
    try:
        from src.pipelines.extract.extract_from_file import run as run_file

        t0 = time.time()
        outputs = run_file()
        elapsed = time.time() - t0
        for name, path in outputs.items():
            results.append({"step": "FILE", "dataset": name, "file": path.name,
                            "status": "OK", "seconds": round(elapsed, 2)})
    except Exception as exc:
        logger.error("File extraction failed: %s", exc)
        results.append({"step": "FILE", "dataset": "-", "file": "-",
                        "status": f"FAIL: {exc}", "seconds": 0})

    # ── Step 3: HTML scraping ───────────────────────────────────
    try:
        from src.pipelines.extract.extract_from_html import run as run_html

        t0 = time.time()
        outputs = run_html()
        elapsed = time.time() - t0
        for name, path in outputs.items():
            results.append({"step": "HTML", "dataset": name, "file": path.name,
                            "status": "OK", "seconds": round(elapsed, 2)})
    except Exception as exc:
        logger.error("HTML extraction failed: %s", exc)
        results.append({"step": "HTML", "dataset": "-", "file": "-",
                        "status": f"FAIL: {exc}", "seconds": 0})

    # ── Step 4: PostgreSQL ──────────────────────────────────────
    try:
        from src.pipelines.extract.extract_from_postgres import run as run_pg

        t0 = time.time()
        outputs = run_pg()
        elapsed = time.time() - t0
        for name, path in outputs.items():
            results.append({"step": "POSTGRES", "dataset": name, "file": path.name,
                            "status": "OK", "seconds": round(elapsed, 2)})
    except Exception as exc:
        logger.error("Postgres extraction failed: %s", exc)
        results.append({"step": "POSTGRES", "dataset": "-", "file": "-",
                        "status": f"FAIL: {exc}", "seconds": 0})

    # ── Step 5: Parquet / DuckDB ────────────────────────────────
    try:
        from src.pipelines.extract.extract_from_parquet import run as run_parquet

        t0 = time.time()
        outputs = run_parquet()
        elapsed = time.time() - t0
        for name, path in outputs.items():
            results.append({"step": "PARQUET", "dataset": name, "file": path.name,
                            "status": "OK", "seconds": round(elapsed, 2)})
    except Exception as exc:
        logger.error("Parquet extraction failed: %s", exc)
        results.append({"step": "PARQUET", "dataset": "-", "file": "-",
                        "status": f"FAIL: {exc}", "seconds": 0})

    # ── Summary ─────────────────────────────────────────────────
    total_elapsed = round(time.time() - total_start, 2)
    ok_count = sum(1 for r in results if r["status"] == "OK")
    fail_count = len(results) - ok_count

    print("\n" + "=" * 65)
    print(f"{'STEP':<12} {'DATASET':<18} {'FILE':<28} {'STATUS'}")
    print("-" * 65)
    for r in results:
        print(f"{r['step']:<12} {r['dataset']:<18} {r['file']:<28} {r['status']}")
    print("=" * 65)
    print(f"Total: {ok_count} OK, {fail_count} FAILED, {total_elapsed}s")
    print(f"Staging dir: {STAGING_DIR}\n")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    run_all()
