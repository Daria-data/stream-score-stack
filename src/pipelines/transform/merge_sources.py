"""Merge cleaned staging sources into unified dimension and fact tables.

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

    Cross-references API reference with country IDs actually used in
    file_results to detect coverage gaps between the two sources.

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

    # Cross-source validation: check results reference only known countries
    if "file_results" in cleaned:
        result_ids = set(cleaned["file_results"]["id_country"].dropna())
        api_ids = set(df["id_country"].dropna())
        missing = result_ids - api_ids
        if missing:
            logger.warning(
                "Countries in results but not in API reference: %d IDs, %s",
                len(missing), sorted(missing)[:10],
            )
        coverage = len(result_ids & api_ids)
        logger.info(
            "Country cross-check: %d/%d result-countries found in API",
            coverage, len(result_ids),
        )

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

    API provides the reference catalog; pg_epreuves carries id_sport per
    épreuve. We validate that every sport referenced in épreuves exists
    in the API catalog and flag gaps.

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
    logger.info("Sports: %d records from API", len(df))

    # Cross-source validation: épreuves reference only known sports
    if "pg_epreuves" in cleaned:
        epr_sport_ids = set(cleaned["pg_epreuves"]["id_sport"].dropna())
        api_sport_ids = set(df["id_sport"].dropna())
        missing = epr_sport_ids - api_sport_ids
        if missing:
            logger.warning(
                "Sports in épreuves but not in API: %d IDs, %s",
                len(missing), sorted(missing)[:10],
            )
        logger.info(
            "Sport cross-check: %d/%d épreuve-sports covered by API catalog",
            len(epr_sport_ids & api_sport_ids), len(epr_sport_ids),
        )

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

    # id_sport is NOT stored here; it lives on dim_epreuve because
    # discipline-to-sport is not a functional dependency (e.g. Lutte, Kayak).
    df = cleaned["pg_epreuves"][
        ["id_discipline", "discipline_name"]
    ].drop_duplicates(subset=["id_discipline"])

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
         "result_direction", "id_discipline", "id_sport"]
    ].copy()
    logger.info("Épreuves: %d records", len(df))
    return df


def merge_editions(
    cleaned: dict[str, pd.DataFrame],
) -> tuple[pd.DataFrame, dict[int, int]]:
    """Build edition dimension from HTML scraping, deduplicated by business key.

    Multiple source records can share the same (season_year, city, competition_type)
    but carry different technical id_edition values.  We collapse them into one
    canonical row per Olympic Games, choosing MIN(id_edition) as the surviving PK.

    Args:
        cleaned: Dict of cleaned DataFrames.

    Returns:
        Tuple of (deduplicated edition DataFrame, old-to-canonical id mapping).
    """
    if "html_editions" not in cleaned:
        logger.warning("html_editions not found in cleaned data")
        return pd.DataFrame(), {}

    df = cleaned["html_editions"].copy()
    logger.info("Editions: %d raw records from HTML", len(df))

    # Cross-source filter: keep editions that have événements
    if "pg_evenements" in cleaned:
        used_editions = set(cleaned["pg_evenements"]["id_edition"].dropna())
        before = len(df)
        df = df[df["id_edition"].isin(used_editions)]
        dropped = before - len(df)
        if dropped:
            logger.info("Editions pruned (no événements): %d removed", dropped)

    biz_key = ["season_year", "city", "host_country", "competition_type"]

    # Canonical id = MIN(id_edition) per business key
    canonical = (
        df.groupby(biz_key, as_index=False)["id_edition"]
        .min()
        .rename(columns={"id_edition": "canonical_id"})
    )

    # Build old-to-canonical mapping for every id_edition in df
    merged = df.merge(canonical, on=biz_key, how="left")
    id_map: dict[int, int] = {}
    for _, row in merged.iterrows():
        old_id = int(row["id_edition"])
        new_id = int(row["canonical_id"])
        if old_id != new_id:
            id_map[old_id] = new_id

    # Keep only the canonical rows (one per Games)
    deduped = (
        df.sort_values("id_edition")
        .drop_duplicates(subset=biz_key, keep="first")
        .reset_index(drop=True)
    )

    logger.info(
        "Editions deduplicated: %d to %d unique Games (%d id_edition remapped)",
        len(df), len(deduped), len(id_map),
    )
    return deduped, id_map


def merge_evenements(
    cleaned: dict[str, pd.DataFrame],
    edition_id_map: dict[int, int] | None = None,
) -> pd.DataFrame:
    """Build événement dimension, remapping edition FKs to canonical IDs.

    Args:
        cleaned: Dict of cleaned DataFrames.
        edition_id_map: Old-to-canonical id_edition mapping from merge_editions.

    Returns:
        Événement dimension DataFrame with consistent id_edition FKs.
    """
    if "pg_evenements" not in cleaned:
        logger.warning("pg_evenements not found in cleaned data")
        return pd.DataFrame()

    df = cleaned["pg_evenements"].copy()

    if edition_id_map:
        before_unique = int(df["id_edition"].nunique())
        df["id_edition"] = df["id_edition"].map(
            lambda x: edition_id_map.get(int(x), x) if pd.notna(x) else x
        )
        after_unique = int(df["id_edition"].nunique())
        remapped = before_unique - after_unique
        if remapped:
            logger.info(
                "Événements: remapped id_edition (%d distinct to %d)",
                before_unique, after_unique,
            )

    logger.info("Événements: %d records", len(df))
    return df


def merge_results(cleaned: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Prepare fact results table with cross-source FK validation.

    Validates that every result row references dimensions that actually
    exist in the other cleaned sources (countries, événements).
    Rows with broken FK references are dropped to guarantee import
    into the target schema will succeed.

    Args:
        cleaned: Dict of cleaned DataFrames.

    Returns:
        Results fact DataFrame with validated foreign keys.
    """
    if "file_results" not in cleaned:
        logger.warning("file_results not found in cleaned data")
        return pd.DataFrame()

    df = cleaned["file_results"].copy()
    initial = len(df)
    logger.info("Results: %d raw records from CSV", initial)

    # FK validation against cleaned dimensions
    fk_checks: list[tuple[str, str, str]] = [
        ("id_country", "api_countries", "id_country"),
        ("id_evenement", "pg_evenements", "id_evenement"),
    ]
    for fk_col, source_key, ref_col in fk_checks:
        if source_key in cleaned and fk_col in df.columns:
            valid = set(cleaned[source_key][ref_col].dropna())
            before = len(df)
            df = df[df[fk_col].isin(valid)]
            dropped = before - len(df)
            if dropped:
                logger.warning(
                    "Results: %d rows dropped (invalid %s not in %s)",
                    dropped, fk_col, source_key,
                )

    logger.info("Results after cross-source FK validation: %d/%d kept", len(df), initial)
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

    editions_df, edition_id_map = merge_editions(cleaned)

    merged: dict[str, pd.DataFrame] = {
        "dim_country": merge_countries(cleaned),
        "dim_federation": merge_federations(cleaned),
        "dim_sport": merge_sports(cleaned),
        "dim_discipline": merge_disciplines(cleaned),
        "dim_epreuve": merge_epreuves(cleaned),
        "dim_edition": editions_df,
        "dim_evenement": merge_evenements(cleaned, edition_id_map),
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
