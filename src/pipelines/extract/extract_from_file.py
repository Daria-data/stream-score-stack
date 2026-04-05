"""Extract result-level rows from the raw CSV into staging (fact + FK columns only).

Only result/fact columns and foreign keys are kept;
dimension data comes from other sources.

Usage:
    uv run python -m src.pipelines.extract.extract_from_file
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent.parent.parent
RAW_CSV = ROOT / "data" / "raw" / "fact_resultats_epreuves.csv"
STAGING_DIR = ROOT / "data" / "staging"

RESULT_COLUMNS = [
    "id_resultat",
    "id_resultat_source",
    "source",
    "id_athlete_base_resultats",
    "id_personne",
    "athlete_nom",
    "athlete_prenom",
    "id_equipe",
    "equipe_en",
    "id_pays",
    "id_epreuve",
    "id_evenement",
    "id_edition",
    "classement_epreuve",
    "performance_finale_texte",
    "performance_finale",
    "dt_creation",
    "dt_modification",
]


def extract_results(csv_path: Path = RAW_CSV) -> pd.DataFrame:
    """Read the raw CSV and select only result-level columns.

    Args:
        csv_path: Path to the source CSV file.

    Returns:
        DataFrame containing fact/result rows with FK references.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Raw CSV not found: {csv_path}")

    logger.info("Reading %s", csv_path.name)
    df = pd.read_csv(csv_path, encoding="utf-8", usecols=RESULT_COLUMNS)
    logger.info("Loaded %d rows, %d columns", len(df), len(df.columns))
    return df


def run(csv_path: Path = RAW_CSV) -> dict[str, Path]:
    """Execute file extraction and save to staging.

    Args:
        csv_path: Path to the source CSV file.

    Returns:
        Mapping of dataset name to output file path.
    """
    STAGING_DIR.mkdir(parents=True, exist_ok=True)

    results = extract_results(csv_path)
    out_path = STAGING_DIR / "file_results.csv"
    results.to_csv(out_path, index=False, encoding="utf-8")
    logger.info("Saved %s (%d rows)", out_path.name, len(results))

    return {"results": out_path}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    run()
