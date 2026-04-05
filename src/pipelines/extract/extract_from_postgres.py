"""Extract épreuves and événements from the PostgreSQL ``source`` schema into staging CSV.

Connects to tables populated at Postgres startup.

Usage:
    uv run python -m src.pipelines.extract.extract_from_postgres
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

STAGING_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "staging"


def _get_engine() -> Engine:
    """Build SQLAlchemy engine from environment variables.

    Returns:
        Configured SQLAlchemy Engine instance.
    """
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5433")
    name = os.getenv("DB_NAME", "sports")
    user = os.getenv("DB_USER", "postgres")
    pwd = os.getenv("DB_PASSWORD", "postgres")
    url = f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{name}"
    return create_engine(url)


def extract_epreuves(engine: Engine) -> pd.DataFrame:
    """Query all rows from source.epreuves.

    Args:
        engine: SQLAlchemy engine connected to the sports database.

    Returns:
        DataFrame with épreuve and discipline/spécialité info.
    """
    sql = "SELECT * FROM source.epreuves ORDER BY id_epreuve"
    logger.info("Executing: %s", sql)
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    logger.info("Extracted %d épreuves", len(df))
    return df


def extract_evenements(engine: Engine) -> pd.DataFrame:
    """Query all rows from source.evenements.

    Args:
        engine: SQLAlchemy engine connected to the sports database.

    Returns:
        DataFrame with événement details.
    """
    sql = "SELECT * FROM source.evenements ORDER BY id_evenement"
    logger.info("Executing: %s", sql)
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    logger.info("Extracted %d événements", len(df))
    return df


def run() -> dict[str, Path]:
    """Execute full PostgreSQL extraction and save to staging.

    Returns:
        Mapping of dataset name to output file path.
    """
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    engine = _get_engine()
    outputs: dict[str, Path] = {}

    epreuves = extract_epreuves(engine)
    path_ep = STAGING_DIR / "pg_epreuves.csv"
    epreuves.to_csv(path_ep, index=False, encoding="utf-8")
    outputs["epreuves"] = path_ep
    logger.info("Saved %s (%d rows)", path_ep.name, len(epreuves))

    evenements = extract_evenements(engine)
    path_ev = STAGING_DIR / "pg_evenements.csv"
    evenements.to_csv(path_ev, index=False, encoding="utf-8")
    outputs["evenements"] = path_ev
    logger.info("Saved %s (%d rows)", path_ev.name, len(evenements))

    engine.dispose()
    return outputs


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    run()
