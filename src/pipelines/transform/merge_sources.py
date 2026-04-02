"""Merge data from multiple staging sources into unified dimension tables.

Covers C10 requirement: aggregation of data from different sources.
Handles:
  - Combining overlapping data (e.g., federations from API and Parquet)
  - Resolving conflicts (prefer more complete records)
  - Building dimension lookup tables

Usage:
    from src.pipelines.transform.merge_sources import merge_all_sources
"""

from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger(__name__)


def merge_countries(cleaned: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Build unified country dimension.

    Args:
        cleaned: Dict of cleaned DataFrames.

    Returns:
        Merged country dimension DataFrame.
    """
    if "api_countries" not in cleaned:
        logger.warning("api_countries not found in cleaned data")
        return pd.DataFrame()

    df = cleaned["api_countries"].copy()
    logger.info("Countries: %d records from API", len(df))
    return df


def merge_federations(cleaned: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Build unified federation dimension from multiple sources.

    Sources: api_sports (has federation info) + parquet_federations.

    Args:
        cleaned: Dict of cleaned DataFrames.

    Returns:
        Merged federation dimension DataFrame.
    """
    frames: list[pd.DataFrame] = []

    # From API sports (has federation columns)
    if "api_sports" in cleaned:
        api_fed = cleaned["api_sports"][
            ["id_federation", "federation_name", "federation_short"]
        ].drop_duplicates(subset=["id_federation"])
        frames.append(api_fed)
        logger.info("Federations: %d from API", len(api_fed))

    # From Parquet
    if "parquet_federations" in cleaned:
        pq_fed = cleaned["parquet_federations"].copy()
        frames.append(pq_fed)
        logger.info("Federations: %d from Parquet", len(pq_fed))

    if not frames:
        logger.warning("No federation sources found")
        return pd.DataFrame()

    # Combine and deduplicate (prefer first occurrence = API if available)
    combined = pd.concat(frames, ignore_index=True)
    merged = combined.drop_duplicates(subset=["id_federation"], keep="first")
    logger.info("Federations merged: %d unique", len(merged))
    return merged


def merge_sports(cleaned: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Build unified sport dimension.

    Args:
        cleaned: Dict of cleaned DataFrames.

    Returns:
        Merged sport dimension DataFrame.
    """
    if "api_sports" not in cleaned:
        logger.warning("api_sports not found in cleaned data")
        return pd.DataFrame()

    df = cleaned["api_sports"][
        ["id_sport", "sport_name_fr", "sport_name_en", "id_federation"]
    ].copy()
    logger.info("Sports: %d records", len(df))
    return df


def merge_disciplines(cleaned: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Build discipline dimension from épreuves source.

    Args:
        cleaned: Dict of cleaned DataFrames.

    Returns:
        Discipline dimension DataFrame.
    """
    if "pg_epreuves" not in cleaned:
        logger.warning("pg_epreuves not found in cleaned data")
        return pd.DataFrame()

    # Extract unique disciplines
    df = cleaned["pg_epreuves"][
        ["id_discipline", "discipline_name"]
    ].drop_duplicates(subset=["id_discipline"])

    # Need to link discipline to sport - this requires the original data
    # For now, we'll leave id_sport as NULL and fill it in build_final
    df["id_sport"] = pd.NA

    logger.info("Disciplines: %d unique", len(df))
    return df


def merge_epreuves(cleaned: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Build épreuve dimension.

    Args:
        cleaned: Dict of cleaned DataFrames.

    Returns:
        Épreuve dimension DataFrame.
    """
    if "pg_epreuves" not in cleaned:
        logger.warning("pg_epreuves not found in cleaned data")
        return pd.DataFrame()

    df = cleaned["pg_epreuves"][
        ["id_epreuve", "epreuve_name", "genre", "epreuve_type",
         "is_individual", "is_olympic", "is_summer", "is_handicap",
         "result_direction", "id_discipline"]
    ].copy()
    logger.info("Épreuves: %d records", len(df))
    return df


def merge_editions(cleaned: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Build edition dimension from HTML scraping.

    Args:
        cleaned: Dict of cleaned DataFrames.

    Returns:
        Edition dimension DataFrame.
    """
    if "html_editions" not in cleaned:
        logger.warning("html_editions not found in cleaned data")
        return pd.DataFrame()

    df = cleaned["html_editions"].copy()
    logger.info("Editions: %d records", len(df))
    return df


def merge_evenements(cleaned: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Build événement dimension.

    Args:
        cleaned: Dict of cleaned DataFrames.

    Returns:
        Événement dimension DataFrame.
    """
    if "pg_evenements" not in cleaned:
        logger.warning("pg_evenements not found in cleaned data")
        return pd.DataFrame()

    df = cleaned["pg_evenements"].copy()
    logger.info("Événements: %d records", len(df))
    return df


def merge_results(cleaned: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Prepare fact results table.

    Args:
        cleaned: Dict of cleaned DataFrames.

    Returns:
        Results fact DataFrame.
    """
    if "file_results" not in cleaned:
        logger.warning("file_results not found in cleaned data")
        return pd.DataFrame()

    df = cleaned["file_results"].copy()
    logger.info("Results: %d records", len(df))
    return df


def merge_all_sources(
    cleaned: dict[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    """Merge all cleaned sources into dimension and fact tables.

    Args:
        cleaned: Dict of source_type -> cleaned DataFrame.

    Returns:
        Dict of table_name -> merged DataFrame.
    """
    logger.info("Merging all sources into unified tables...")

    merged: dict[str, pd.DataFrame] = {
        "dim_country": merge_countries(cleaned),
        "dim_federation": merge_federations(cleaned),
        "dim_sport": merge_sports(cleaned),
        "dim_discipline": merge_disciplines(cleaned),
        "dim_epreuve": merge_epreuves(cleaned),
        "dim_edition": merge_editions(cleaned),
        "dim_evenement": merge_evenements(cleaned),
        "fact_result": merge_results(cleaned),
    }

    print("\nMerge Summary:")
    print("-" * 40)
    for name, df in merged.items():
        print(f"  {name}: {len(df)} rows")

    return merged


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    from src.pipelines.transform.normalize_columns import normalize_all_staging
    from src.pipelines.transform.clean_records import clean_all_normalized

    normalized = normalize_all_staging()
    cleaned, _ = clean_all_normalized(normalized)
    merged = merge_all_sources(cleaned)
