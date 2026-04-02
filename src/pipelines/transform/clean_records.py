"""Clean records: remove nulls, duplicates, and invalid entries.

Covers C10 requirement: suppression des entrées corrompues.
Handles:
  - Removal of rows with NULL critical fields
  - Deduplication by primary key
  - Validation of foreign key references
  - Logging of removed records

Usage:
    from src.pipelines.transform.clean_records import clean_dataframe
"""

from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger(__name__)

# Critical fields by source type (rows with NULL in these are dropped)
CRITICAL_FIELDS: dict[str, list[str]] = {
    "api_countries": ["id_country", "country_name"],
    "api_sports": ["id_sport", "sport_name_en"],
    "html_editions": ["id_edition", "start_date", "city"],
    "parquet_athletes": ["id_athlete"],
    "parquet_federations": ["id_federation"],
    "pg_epreuves": ["id_epreuve", "epreuve_name", "id_discipline"],
    "pg_evenements": ["id_evenement", "id_epreuve", "id_edition"],
    "file_results": ["id_result", "id_evenement", "id_country"],
}

# Primary key columns for deduplication
PRIMARY_KEYS: dict[str, str] = {
    "api_countries": "id_country",
    "api_sports": "id_sport",
    "html_editions": "id_edition",
    "parquet_athletes": "id_athlete",
    "parquet_federations": "id_federation",
    "pg_epreuves": "id_epreuve",
    "pg_evenements": "id_evenement",
    "file_results": "id_result",
}


def remove_null_critical(
    df: pd.DataFrame,
    critical_fields: list[str],
) -> tuple[pd.DataFrame, int]:
    """Remove rows with NULL values in critical fields.

    Args:
        df: Input DataFrame.
        critical_fields: List of column names that must not be NULL.

    Returns:
        Tuple of (cleaned DataFrame, number of removed rows).
    """
    initial_count = len(df)

    # Only check columns that exist
    fields_to_check = [f for f in critical_fields if f in df.columns]
    if not fields_to_check:
        return df, 0

    df_clean = df.dropna(subset=fields_to_check)
    removed = initial_count - len(df_clean)

    if removed > 0:
        logger.info("  Removed %d rows with NULL in %s", removed, fields_to_check)

    return df_clean, removed


def remove_duplicates(
    df: pd.DataFrame,
    key_column: str,
) -> tuple[pd.DataFrame, int]:
    """Remove duplicate rows based on primary key.

    Args:
        df: Input DataFrame.
        key_column: Column name to use as primary key.

    Returns:
        Tuple of (deduplicated DataFrame, number of removed duplicates).
    """
    if key_column not in df.columns:
        return df, 0

    initial_count = len(df)
    df_clean = df.drop_duplicates(subset=[key_column], keep="first")
    removed = initial_count - len(df_clean)

    if removed > 0:
        logger.info("  Removed %d duplicate rows by '%s'", removed, key_column)

    return df_clean, removed


def validate_foreign_keys(
    df: pd.DataFrame,
    fk_column: str,
    valid_keys: set[int],
) -> tuple[pd.DataFrame, int]:
    """Remove rows with invalid foreign key references.

    Args:
        df: Input DataFrame.
        fk_column: Foreign key column name.
        valid_keys: Set of valid key values.

    Returns:
        Tuple of (validated DataFrame, number of removed rows).
    """
    if fk_column not in df.columns:
        return df, 0

    initial_count = len(df)
    # Handle nullable foreign keys
    mask = df[fk_column].isna() | df[fk_column].isin(valid_keys)
    df_clean = df[mask]
    removed = initial_count - len(df_clean)

    if removed > 0:
        logger.info("  Removed %d rows with invalid '%s' references", removed, fk_column)

    return df_clean, removed


def clean_dataframe(
    df: pd.DataFrame,
    source_type: str,
    valid_fks: dict[str, set[int]] | None = None,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Apply all cleaning rules to a DataFrame.

    Args:
        df: Normalized DataFrame.
        source_type: Key identifying the source.
        valid_fks: Optional dict of {fk_column: set_of_valid_values}.

    Returns:
        Tuple of (cleaned DataFrame, stats dict with removal counts).
    """
    logger.info("Cleaning %s (%d rows)", source_type, len(df))
    stats: dict[str, int] = {"initial": len(df)}

    # Remove NULL critical fields
    critical = CRITICAL_FIELDS.get(source_type, [])
    df, null_removed = remove_null_critical(df, critical)
    stats["null_removed"] = null_removed

    # Remove duplicates
    pk = PRIMARY_KEYS.get(source_type)
    if pk:
        df, dup_removed = remove_duplicates(df, pk)
        stats["duplicates_removed"] = dup_removed
    else:
        stats["duplicates_removed"] = 0

    # Validate foreign keys if provided
    fk_removed = 0
    if valid_fks:
        for fk_col, valid_set in valid_fks.items():
            df, removed = validate_foreign_keys(df, fk_col, valid_set)
            fk_removed += removed
    stats["fk_invalid_removed"] = fk_removed

    stats["final"] = len(df)
    stats["total_removed"] = stats["initial"] - stats["final"]

    logger.info("  Final: %d rows (removed %d total)", stats["final"], stats["total_removed"])
    return df, stats


def clean_all_normalized(
    normalized: dict[str, pd.DataFrame],
) -> tuple[dict[str, pd.DataFrame], dict[str, dict[str, int]]]:
    """Clean all normalized DataFrames with FK validation.

    Args:
        normalized: Dict of source_type -> normalized DataFrame.

    Returns:
        Tuple of (cleaned DataFrames dict, cleaning stats dict).
    """
    cleaned: dict[str, pd.DataFrame] = {}
    all_stats: dict[str, dict[str, int]] = {}

    # First pass: clean dimension tables (no FK validation needed)
    dim_sources = ["api_countries", "api_sports", "html_editions",
                   "parquet_athletes", "parquet_federations",
                   "pg_epreuves", "pg_evenements"]

    for source in dim_sources:
        if source in normalized:
            cleaned[source], all_stats[source] = clean_dataframe(
                normalized[source], source
            )

    # Build valid FK sets from cleaned dimensions
    valid_fks: dict[str, set[int]] = {}

    if "api_countries" in cleaned:
        valid_fks["id_country"] = set(cleaned["api_countries"]["id_country"].dropna())

    if "pg_evenements" in cleaned:
        valid_fks["id_evenement"] = set(cleaned["pg_evenements"]["id_evenement"].dropna())

    if "html_editions" in cleaned:
        valid_fks["id_edition"] = set(cleaned["html_editions"]["id_edition"].dropna())

    # Second pass: clean fact table with FK validation
    if "file_results" in normalized:
        cleaned["file_results"], all_stats["file_results"] = clean_dataframe(
            normalized["file_results"], "file_results", valid_fks
        )

    return cleaned, all_stats


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    from src.pipelines.transform.normalize_columns import normalize_all_staging

    normalized = normalize_all_staging()
    cleaned, stats = clean_all_normalized(normalized)

    print("\nCleaning Summary:")
    print("-" * 60)
    for source, s in stats.items():
        print(f"{source}: {s['initial']} -> {s['final']} ({s['total_removed']} removed)")
