"""Normalize column names and data types across all staging sources.

Covers C10 requirement: homogenization of data formats.
Standardizes:
  - Column names (snake_case, consistent naming)
  - Date formats (ISO 8601)
  - Numeric types (int/float where appropriate)
  - String encoding (UTF-8, trimmed)

Usage:
    from src.pipelines.transform.normalize_columns import normalize_dataframe
"""

from __future__ import annotations

import logging
import re
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

# Column renaming maps for each source type
COLUMN_MAPS: dict[str, dict[str, str]] = {
    "api_countries": {
        "id_pays": "id_country",
        "country_name": "country_name",
    },
    "api_sports": {
        "id_sport": "id_sport",
        "sport": "sport_name_fr",
        "sport_en": "sport_name_en",
        "id_federation": "id_federation",
        "federation": "federation_name",
        "federation_nom_court": "federation_short",
    },
    "html_editions": {
        "id_edition": "id_edition",
        "season": "season_year",
        "start_date": "start_date",
        "end_date": "end_date",
        "id_city": "id_city",
        "city": "city",
        "host_country": "host_country",
        "competition_type": "competition_type",
    },
    "parquet_athletes": {
        "id_athlete_base_resultats": "id_athlete",
        "athlete_nom": "athlete_last_name",
        "athlete_prenom": "athlete_first_name",
        "id_equipe": "id_team",
        "equipe_en": "team_name",
    },
    "parquet_federations": {
        "id_federation": "id_federation",
        "federation": "federation_name",
        "federation_nom_court": "federation_short",
    },
    "pg_epreuves": {
        "id_epreuve": "id_epreuve",
        "epreuve": "epreuve_name",
        "epreuve_genre": "genre",
        "epreuve_type": "epreuve_type",
        "est_epreuve_individuelle": "is_individual",
        "est_epreuve_olympique": "is_olympic",
        "est_epreuve_ete": "is_summer",
        "est_epreuve_handi": "is_handicap",
        "epreuve_sens_resultat": "result_direction",
        "id_discipline_administrative": "id_discipline",
        "discipline_administrative": "discipline_name",
        "id_specialite": "id_specialite",
        "specialite": "specialite_name",
        "id_sport": "id_sport",
    },
    "pg_evenements": {
        "id_evenement": "id_evenement",
        "evenement": "event_name_fr",
        "evenement_en": "event_name_en",
        "categorie_age": "age_category",
        "id_epreuve": "id_epreuve",
        "id_edition": "id_edition",
    },
    "file_results": {
        "id_resultat": "id_result",
        "id_resultat_source": "source_id",
        "source": "data_source",
        "id_athlete_base_resultats": "id_athlete",
        "id_personne": "id_person",
        "athlete_nom": "athlete_last_name",
        "athlete_prenom": "athlete_first_name",
        "id_equipe": "id_team",
        "equipe_en": "team_name",
        "id_pays": "id_country",
        "id_epreuve": "id_epreuve",
        "id_evenement": "id_evenement",
        "id_edition": "id_edition",
        "classement_epreuve": "rank",
        "performance_finale_texte": "performance_text",
        "performance_finale": "performance_value",
        "dt_creation": "created_at",
        "dt_modification": "updated_at",
    },
}

# Date columns to parse
DATE_COLUMNS = ["start_date", "end_date", "created_at", "updated_at"]

# Boolean columns (0/1 -> True/False)
BOOLEAN_COLUMNS = ["is_individual", "is_olympic", "is_summer", "is_handicap"]

# Integer columns
INTEGER_COLUMNS = [
    "id_country", "id_sport", "id_federation", "id_edition", "id_city",
    "id_epreuve", "id_discipline", "id_specialite", "id_evenement",
    "id_athlete", "id_team", "id_person", "id_result", "rank",
    "season_year", "result_direction",
]


def _clean_string(value: Any) -> str | None:
    """Clean and normalize string values.

    Args:
        value: Raw value from DataFrame.

    Returns:
        Cleaned string or None if empty/null.
    """
    if pd.isna(value):
        return None
    s = str(value).strip()
    if s.lower() in ("", "null", "none", "nan"):
        return None
    return s


def _to_snake_case(name: str) -> str:
    """Convert column name to snake_case.

    Args:
        name: Original column name.

    Returns:
        snake_case version.
    """
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def normalize_dataframe(
    df: pd.DataFrame,
    source_type: str,
) -> pd.DataFrame:
    """Normalize a DataFrame from a specific source.

    Args:
        df: Raw DataFrame from staging.
        source_type: Key identifying the source (e.g., 'api_countries').

    Returns:
        Normalized DataFrame with standardized columns and types.
    """
    df = df.copy()
    logger.info("Normalizing %s (%d rows, %d cols)", source_type, len(df), len(df.columns))

    # Rename columns if mapping exists
    if source_type in COLUMN_MAPS:
        col_map = COLUMN_MAPS[source_type]
        # Only rename columns that exist
        rename_map = {k: v for k, v in col_map.items() if k in df.columns}
        df = df.rename(columns=rename_map)
        logger.info("  Renamed %d columns", len(rename_map))

    # Clean string columns
    str_cols = df.select_dtypes(include=["object"]).columns
    for col in str_cols:
        df[col] = df[col].apply(_clean_string)

    # Parse date columns
    for col in DATE_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
            logger.info("  Parsed dates in '%s'", col)

    # Convert boolean columns
    for col in BOOLEAN_COLUMNS:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: bool(int(x)) if pd.notna(x) else None)
            logger.info("  Converted booleans in '%s'", col)

    # Convert integer columns (with nullable Int64)
    for col in INTEGER_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    logger.info("  Final shape: %d rows, %d cols", len(df), len(df.columns))
    return df


def normalize_all_staging(staging_dir: str | None = None) -> dict[str, pd.DataFrame]:
    """Load and normalize all CSV files from staging directory.

    Args:
        staging_dir: Path to staging directory. Uses default if None.

    Returns:
        Dictionary mapping source names to normalized DataFrames.
    """
    from pathlib import Path

    if staging_dir is None:
        staging_dir = Path(__file__).resolve().parent.parent.parent.parent / "data" / "staging"
    else:
        staging_dir = Path(staging_dir)

    normalized: dict[str, pd.DataFrame] = {}

    for csv_file in staging_dir.glob("*.csv"):
        # Extract source type from filename (e.g., 'api_countries' from 'api_countries.csv')
        source_type = csv_file.stem

        # Skip sql_* files (they are query outputs, not primary sources)
        if source_type.startswith("sql_"):
            continue

        logger.info("Loading %s", csv_file.name)
        df = pd.read_csv(csv_file, encoding="utf-8")
        normalized[source_type] = normalize_dataframe(df, source_type)

    return normalized


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    result = normalize_all_staging()
    print(f"\nNormalized {len(result)} sources:")
    for name, df in result.items():
        print(f"  {name}: {len(df)} rows, {len(df.columns)} cols")
