"""Mock API — simulates an external sports reference data service.

Serves countries and sports/disciplines as JSON via REST endpoints.
Used as one of 5 data sources for the E4 extraction pipeline.

Usage (local):
    uvicorn src.mock_api.main:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query

app = FastAPI(
    title="Sports Reference API",
    description="Mock external API providing country and sport reference data.",
    version="1.0.0",
)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "mock_api"

_countries: list[dict[str, Any]] = []
_sports: list[dict[str, Any]] = []


def _load_data() -> None:
    """Load JSON files into memory at startup."""
    global _countries, _sports
    _countries = json.loads((DATA_DIR / "countries.json").read_text(encoding="utf-8"))
    _sports = json.loads((DATA_DIR / "sports.json").read_text(encoding="utf-8"))


@app.on_event("startup")
async def startup() -> None:
    """Trigger data loading on application start."""
    _load_data()


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        Simple status message.
    """
    return {"status": "ok"}


@app.get("/countries")
async def get_countries(
    limit: int = Query(default=0, ge=0, description="Max records to return (0 = all)"),
) -> list[dict[str, Any]]:
    """Return the list of countries.

    Args:
        limit: Maximum number of records. 0 means no limit.

    Returns:
        List of country objects with id_pays and country_name.
    """
    if limit > 0:
        return _countries[:limit]
    return _countries


@app.get("/countries/{country_id}")
async def get_country(country_id: int) -> dict[str, Any]:
    """Return a single country by ID.

    Args:
        country_id: The id_pays value.

    Returns:
        Country object.

    Raises:
        HTTPException: If country not found.
    """
    for c in _countries:
        if c["id_pays"] == country_id:
            return c
    raise HTTPException(status_code=404, detail=f"Country {country_id} not found")


@app.get("/sports")
async def get_sports(
    limit: int = Query(default=0, ge=0, description="Max records to return (0 = all)"),
) -> list[dict[str, Any]]:
    """Return the list of sports with federation info.

    Args:
        limit: Maximum number of records. 0 means no limit.

    Returns:
        List of sport objects.
    """
    if limit > 0:
        return _sports[:limit]
    return _sports


@app.get("/sports/{sport_id}")
async def get_sport(sport_id: int) -> dict[str, Any]:
    """Return a single sport by ID.

    Args:
        sport_id: The id_sport value.

    Returns:
        Sport object.

    Raises:
        HTTPException: If sport not found.
    """
    for s in _sports:
        if s["id_sport"] == sport_id:
            return s
    raise HTTPException(status_code=404, detail=f"Sport {sport_id} not found")
