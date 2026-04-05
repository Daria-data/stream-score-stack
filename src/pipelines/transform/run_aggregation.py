"""Orchestrate the full aggregation pipeline.

Runs: normalize -> clean -> merge -> build_final.
Produces summary report and saves outputs to data/final/.

Usage:
    uv run python -m src.pipelines.transform.run_aggregation
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent.parent.parent
STAGING_DIR = ROOT / "data" / "staging"
FINAL_DIR = ROOT / "data" / "final"


def run_full_pipeline() -> None:
    """Execute the complete aggregation pipeline with timing."""
    from src.pipelines.transform.normalize_columns import normalize_all_staging
    from src.pipelines.transform.clean_records import clean_all_normalized
    from src.pipelines.transform.merge_sources import merge_all_sources
    from src.pipelines.transform.build_final_dataset import build_final

    total_start = time.time()

    print("\n" + "=" * 70)
    print("  AGGREGATION + CLEANING PIPELINE")
    print("  Inputs: data/staging/*.csv")
    print("  Outputs: data/final/*.csv, data/final/final_dataset.parquet")
    print("=" * 70)

    # Step 1: Normalize
    print("\n[1/4] NORMALIZE: Standardizing column names and types...")
    t0 = time.time()
    normalized = normalize_all_staging()
    t_normalize = round(time.time() - t0, 2)
    print(f"      Normalized {len(normalized)} sources in {t_normalize}s")

    # Step 2: Clean
    print("\n[2/4] CLEAN: Removing nulls, duplicates, invalid records...")
    t0 = time.time()
    cleaned, stats = clean_all_normalized(normalized)
    t_clean = round(time.time() - t0, 2)

    total_removed = sum(s.get("total_removed", 0) for s in stats.values())
    print(f"      Cleaned {len(cleaned)} sources, removed {total_removed} invalid rows in {t_clean}s")

    # Detailed stats
    print("\n      Cleaning details:")
    for source, s in stats.items():
        if s.get("total_removed", 0) > 0:
            print(f"        {source}: {s['initial']} -> {s['final']} "
                  f"(nulls: {s.get('null_removed', 0)}, dups: {s.get('duplicates_removed', 0)})")

    # Step 3: Merge
    print("\n[3/4] MERGE: Combining sources into unified tables...")
    t0 = time.time()
    merged = merge_all_sources(cleaned)
    t_merge = round(time.time() - t0, 2)
    print(f"      Merged into {len(merged)} tables in {t_merge}s")

    # Step 4: Build final
    print("\n[4/4] BUILD: Saving final dataset files...")
    t0 = time.time()
    outputs = build_final(merged)
    t_build = round(time.time() - t0, 2)
    print(f"      Saved {len(outputs)} output files in {t_build}s")

    # Summary
    total_time = round(time.time() - total_start, 2)

    print("\n" + "=" * 70)
    print("  PIPELINE COMPLETE")
    print("-" * 70)
    print(f"  Total time: {total_time}s")
    print(f"  Output directory: {FINAL_DIR}")
    print("\n  Output files:")
    for name, path in outputs.items():
        size_kb = round(path.stat().st_size / 1024, 1) if path.exists() else 0
        print(f"    {path.name}: {size_kb} KB")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    run_full_pipeline()
