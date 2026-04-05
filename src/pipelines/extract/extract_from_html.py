"""Extract Olympic editions from a local HTML table via BeautifulSoup.

Usage:
    uv run python -m src.pipelines.extract.extract_from_html
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent.parent.parent
HTML_PATH = ROOT / "data" / "html" / "editions.html"
STAGING_DIR = ROOT / "data" / "staging"


def extract_editions(html_path: Path = HTML_PATH) -> pd.DataFrame:
    """Parse the HTML table and return edition records.

    Args:
        html_path: Path to the local HTML file containing the editions table.

    Returns:
        DataFrame with edition columns (id, season, dates, city, etc.).

    Raises:
        FileNotFoundError: If the HTML file does not exist.
        ValueError: If no table with id='editions' is found.
    """
    if not html_path.exists():
        raise FileNotFoundError(f"HTML file not found: {html_path}")

    logger.info("Parsing %s", html_path.name)
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")

    table = soup.find("table", id="editions")
    if table is None:
        raise ValueError("No <table id='editions'> found in the HTML file")

    headers = [th.get_text(strip=True) for th in table.find("thead").find_all("th")]

    rows: list[list[str]] = []
    for tr in table.find("tbody").find_all("tr"):
        cells = [td.get_text(strip=True) for td in tr.find_all("td")]
        rows.append(cells)

    df = pd.DataFrame(rows, columns=headers)
    logger.info("Scraped %d edition rows", len(df))
    return df


def run(html_path: Path = HTML_PATH) -> dict[str, Path]:
    """Execute HTML scraping and save results to staging.

    Args:
        html_path: Path to the local HTML file.

    Returns:
        Mapping of dataset name to output file path.
    """
    STAGING_DIR.mkdir(parents=True, exist_ok=True)

    editions = extract_editions(html_path)
    out_path = STAGING_DIR / "html_editions.csv"
    editions.to_csv(out_path, index=False, encoding="utf-8")
    logger.info("Saved %s (%d rows)", out_path.name, len(editions))

    return {"editions": out_path}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    run()
