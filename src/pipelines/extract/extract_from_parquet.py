"""Extract athletes, teams, and federations from a Parquet file via DuckDB.

Covers C8 requirement: extraction from a big-data / analytical system.
DuckDB provides columnar SQL queries on Parquet — a lightweight
alternative to Spark/Hive suitable for analytical workloads.

Usage:
    uv run python -m src.pipelines.extract.extract_from_parquet
"""

from __future__ import annotations

import logging
from pathlib import Path

import duckdb
import pandas as pd

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent.parent.parent
PARQUET_PATH = ROOT / "data" / "parquet" / "athletes_teams.parquet"
STAGING_DIR = ROOT / "data" / "staging"


def extract_athletes(parquet_path: Path = PARQUET_PATH) -> pd.DataFrame:
    """Run a DuckDB SQL query on the Parquet file to get unique athletes.

    Args:
        parquet_path: Path to the athletes_teams Parquet file.

    Returns:
        DataFrame with deduplicated athlete records.

    Raises:
        FileNotFoundError: If the Parquet file does not exist.
    """
    if not parquet_path.exists():
        raise FileNotFoundError(f"Parquet file not found: {parquet_path}")

    path_str = str(parquet_path).replace("\\", "/")

    query = f"""
        SELECT DISTINCT
            id_athlete_base_resultats,
            athlete_nom,
            athlete_prenom,
            id_equipe,
            equipe_en
        FROM read_parquet('{path_str}')
        WHERE id_athlete_base_resultats IS NOT NULL
        ORDER BY id_athlete_base_resultats
    """

    logger.info("DuckDB query on %s", parquet_path.name)
    conn = duckdb.connect()
    df = conn.execute(query).df()
    conn.close()
    logger.info("Extracted %d athlete records", len(df))
    return df


def extract_federations(parquet_path: Path = PARQUET_PATH) -> pd.DataFrame:
    """Run a DuckDB SQL query to get unique federations.

    Args:
        parquet_path: Path to the athletes_teams Parquet file.

    Returns:
        DataFrame with deduplicated federation records.

    Raises:
        FileNotFoundError: If the Parquet file does not exist.
    """
    if not parquet_path.exists():
        raise FileNotFoundError(f"Parquet file not found: {parquet_path}")

    path_str = str(parquet_path).replace("\\", "/")

    query = f"""
        SELECT DISTINCT
            id_federation,
            federation,
            federation_nom_court
        FROM read_parquet('{path_str}')
        ORDER BY id_federation
    """

    logger.info("DuckDB query on %s (federations)", parquet_path.name)
    conn = duckdb.connect()
    df = conn.execute(query).df()
    conn.close()
    logger.info("Extracted %d federations", len(df))
    return df


def run(parquet_path: Path = PARQUET_PATH) -> dict[str, Path]:
    """Execute full Parquet extraction and save to staging.

    Args:
        parquet_path: Path to the Parquet source file.

    Returns:
        Mapping of dataset name to output file path.
    """
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, Path] = {}

    athletes = extract_athletes(parquet_path)
    path_a = STAGING_DIR / "parquet_athletes.csv"
    athletes.to_csv(path_a, index=False, encoding="utf-8")
    outputs["athletes"] = path_a
    logger.info("Saved %s (%d rows)", path_a.name, len(athletes))

    federations = extract_federations(parquet_path)
    path_f = STAGING_DIR / "parquet_federations.csv"
    federations.to_csv(path_f, index=False, encoding="utf-8")
    outputs["federations"] = path_f
    logger.info("Saved %s (%d rows)", path_f.name, len(federations))

    return outputs


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    run()
