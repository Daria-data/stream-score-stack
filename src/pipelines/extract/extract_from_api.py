"""Extract reference data (countries, sports) from the mock REST API into staging CSV.

Usage:
    uv run python -m src.pipelines.extract.extract_from_api
"""

from __future__ import annotations

import logging
from pathlib import Path

import httpx
import pandas as pd

logger = logging.getLogger(__name__)

STAGING_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "staging"
DEFAULT_BASE_URL = "http://localhost:8000"


def extract_countries(base_url: str = DEFAULT_BASE_URL) -> pd.DataFrame:
    """Fetch country list from the mock API.

    Args:
        base_url: Root URL of the mock API service.

    Returns:
        DataFrame with columns [id_pays, country_name].

    Raises:
        httpx.HTTPStatusError: If the API returns a non-2xx status.
    """
    url = f"{base_url}/countries"
    logger.info("GET %s", url)
    resp = httpx.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    df = pd.DataFrame(data)
    logger.info("Received %d countries", len(df))
    return df


def extract_sports(base_url: str = DEFAULT_BASE_URL) -> pd.DataFrame:
    """Fetch sport list from the mock API.

    Args:
        base_url: Root URL of the mock API service.

    Returns:
        DataFrame with sport and federation columns.

    Raises:
        httpx.HTTPStatusError: If the API returns a non-2xx status.
    """
    url = f"{base_url}/sports"
    logger.info("GET %s", url)
    resp = httpx.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    df = pd.DataFrame(data)
    logger.info("Received %d sports", len(df))
    return df


def run(base_url: str = DEFAULT_BASE_URL) -> dict[str, Path]:
    """Execute full API extraction and save results to staging.

    Args:
        base_url: Root URL of the mock API service.

    Returns:
        Mapping of dataset name to output file path.
    """
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, Path] = {}

    countries = extract_countries(base_url)
    path_c = STAGING_DIR / "api_countries.csv"
    countries.to_csv(path_c, index=False, encoding="utf-8")
    outputs["countries"] = path_c
    logger.info("Saved %s (%d rows)", path_c.name, len(countries))

    sports = extract_sports(base_url)
    path_s = STAGING_DIR / "api_sports.csv"
    sports.to_csv(path_s, index=False, encoding="utf-8")
    outputs["sports"] = path_s
    logger.info("Saved %s (%d rows)", path_s.name, len(sports))

    return outputs


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    run()
