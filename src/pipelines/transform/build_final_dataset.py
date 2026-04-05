"""Assemble the final normalized dataset ready for database import.

Covers C10 requirement: build final aggregated dataset.
Outputs:
  - data/final/dim_*.csv (dimension tables)
  - data/final/fact_result.csv (fact table)
  - data/final/final_dataset.parquet (combined for analytics)

Usage:
    from src.pipelines.transform.build_final_dataset import build_final
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent.parent.parent
FINAL_DIR = ROOT / "data" / "final"


def _safe_select(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Select columns that exist in the DataFrame.

    Args:
        df: Input DataFrame.
        columns: Desired columns.

    Returns:
        DataFrame with available columns only.
    """
    available = [c for c in columns if c in df.columns]
    return df[available].copy() if available else pd.DataFrame()


def align_columns_to_schema(
    merged: dict[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    """Align merged DataFrames to match target database schema.

    Args:
        merged: Dict of merged DataFrames.

    Returns:
        Dict with columns aligned to sql/init_target_db.sql schema.
    """
    aligned: dict[str, pd.DataFrame] = {}

    # dim_country
    if "dim_country" in merged and not merged["dim_country"].empty:
        aligned["dim_country"] = _safe_select(
            merged["dim_country"], ["id_country", "country_name"]
        )

    # dim_federation
    if "dim_federation" in merged and not merged["dim_federation"].empty:
        aligned["dim_federation"] = _safe_select(
            merged["dim_federation"], ["id_federation", "federation_name", "federation_short"]
        )

    # dim_sport
    if "dim_sport" in merged and not merged["dim_sport"].empty:
        aligned["dim_sport"] = _safe_select(
            merged["dim_sport"],
            ["id_sport", "sport_name_fr", "sport_name_en", "id_federation"]
        )

    # dim_discipline (no id_sport — see dim_epreuve)
    if "dim_discipline" in merged and not merged["dim_discipline"].empty:
        aligned["dim_discipline"] = _safe_select(
            merged["dim_discipline"],
            ["id_discipline", "discipline_name"]
        )

    # dim_epreuve (id_sport lives here, not on discipline)
    if "dim_epreuve" in merged and not merged["dim_epreuve"].empty:
        aligned["dim_epreuve"] = _safe_select(
            merged["dim_epreuve"],
            ["id_epreuve", "epreuve_name", "genre", "epreuve_type",
             "is_individual", "is_olympic", "is_summer", "is_handicap",
             "result_direction", "id_discipline", "id_sport"]
        )

    # dim_edition
    if "dim_edition" in merged and not merged["dim_edition"].empty:
        aligned["dim_edition"] = _safe_select(
            merged["dim_edition"],
            ["id_edition", "season_year", "start_date", "end_date",
             "city", "host_country", "competition_type"]
        )

    # dim_evenement
    if "dim_evenement" in merged and not merged["dim_evenement"].empty:
        aligned["dim_evenement"] = _safe_select(
            merged["dim_evenement"],
            ["id_evenement", "event_name_fr", "event_name_en",
             "age_category", "id_epreuve", "id_edition"]
        )

    # fact_result
    if "fact_result" in merged and not merged["fact_result"].empty:
        aligned["fact_result"] = _safe_select(
            merged["fact_result"],
            ["id_result", "id_evenement", "id_country", "id_athlete",
             "athlete_last_name", "athlete_first_name", "id_team", "team_name",
             "rank", "performance_text", "performance_value", "source_id",
             "created_at", "updated_at"]
        )

    return aligned


def save_to_csv(aligned: dict[str, pd.DataFrame], output_dir: Path) -> list[Path]:
    """Save aligned DataFrames as CSV files.

    Args:
        aligned: Dict of table_name -> DataFrame.
        output_dir: Directory to save CSV files.

    Returns:
        List of saved file paths.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []

    for name, df in aligned.items():
        if df.empty:
            logger.warning("Skipping %s (empty)", name)
            continue
        path = output_dir / f"{name}.csv"
        df.to_csv(path, index=False, encoding="utf-8")
        saved.append(path)
        logger.info("Saved %s (%d rows)", path.name, len(df))

    return saved


def save_combined_parquet(aligned: dict[str, pd.DataFrame], output_dir: Path) -> Path:
    """Save a combined parquet file with all data for analytics.

    Args:
        aligned: Dict of table_name -> DataFrame.
        output_dir: Directory to save parquet file.

    Returns:
        Path to saved parquet file.
    """
    # For the combined file, we denormalize fact_result with key dimensions
    if "fact_result" not in aligned:
        logger.warning("fact_result not in aligned data, skipping parquet")
        return Path()

    fact = aligned["fact_result"].copy()

    # Add country name
    if "dim_country" in aligned:
        fact = fact.merge(
            aligned["dim_country"][["id_country", "country_name"]],
            on="id_country",
            how="left",
        )

    # Add edition info
    if "dim_edition" in aligned:
        fact = fact.merge(
            aligned["dim_edition"][["id_edition", "season_year", "city", "competition_type"]],
            left_on="id_evenement",  # Need to go through evenement
            right_on="id_edition",
            how="left",
            suffixes=("", "_edition"),
        )

    path = output_dir / "final_dataset.parquet"
    fact.to_parquet(path, index=False, engine="pyarrow")
    logger.info("Saved combined parquet: %s (%d rows)", path.name, len(fact))
    return path


def build_final(merged: dict[str, pd.DataFrame]) -> dict[str, Path]:
    """Build and save all final dataset files.

    Args:
        merged: Dict of merged DataFrames from merge_sources.

    Returns:
        Dict mapping output type to file path.
    """
    logger.info("Building final dataset...")

    aligned = align_columns_to_schema(merged)

    outputs: dict[str, Path] = {}

    # Save individual CSV files
    csv_paths = save_to_csv(aligned, FINAL_DIR)
    for p in csv_paths:
        outputs[p.stem] = p

    # Save combined parquet
    parquet_path = save_combined_parquet(aligned, FINAL_DIR)
    if parquet_path.exists():
        outputs["final_parquet"] = parquet_path

    return outputs


def run() -> dict[str, Path]:
    """Execute full build pipeline: normalize -> clean -> merge -> build.

    Returns:
        Dict of output file paths.
    """
    from src.pipelines.transform.normalize_columns import normalize_all_staging
    from src.pipelines.transform.clean_records import clean_all_normalized
    from src.pipelines.transform.merge_sources import merge_all_sources

    print("\n" + "=" * 60)
    print("AGGREGATION PIPELINE — Building Final Dataset (C10)")
    print("=" * 60)

    print("\n[Step 1] Normalizing staging data...")
    normalized = normalize_all_staging()

    print("\n[Step 2] Cleaning records...")
    cleaned, stats = clean_all_normalized(normalized)

    print("\n[Step 3] Merging sources...")
    merged = merge_all_sources(cleaned)

    print("\n[Step 4] Building final dataset...")
    outputs = build_final(merged)

    print("\n" + "=" * 60)
    print("OUTPUT FILES:")
    for name, path in outputs.items():
        print(f"  {name}: {path}")
    print("=" * 60 + "\n")

    return outputs


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    run()
