"""REST API route definitions for the Olympic results dataset.

All data endpoints require a valid API key (X-API-Key header).
Authenticated read access to dimension and fact data.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.api.auth import verify_api_key
from src.api.db import get_db
from src.api.schemas import (
    CountryOut,
    EditionOut,
    FederationOut,
    MedalCount,
    PaginatedResults,
    ResultDetail,
    ResultOut,
    SportOut,
)

router = APIRouter()


# ── Health (no auth) ─────────────────────────────────────────────

@router.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    """Health check: no authentication required.

    Returns:
        Simple status dict.
    """
    return {"status": "ok", "service": "sports-api"}


# ── Countries ────────────────────────────────────────────────────

@router.get(
    "/countries",
    response_model=list[CountryOut],
    tags=["dimensions"],
    dependencies=[Depends(verify_api_key)],
)
def list_countries(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[dict]:
    """List countries with pagination.

    Args:
        limit: Max records per page.
        offset: Number of records to skip.
        db: Injected DB session.

    Returns:
        List of country records.
    """
    rows = db.execute(
        text("SELECT id_country, country_name FROM dim_country ORDER BY country_name LIMIT :lim OFFSET :off"),
        {"lim": limit, "off": offset},
    )
    return [dict(r._mapping) for r in rows]


@router.get(
    "/countries/{country_id}",
    response_model=CountryOut,
    tags=["dimensions"],
    dependencies=[Depends(verify_api_key)],
)
def get_country(country_id: int, db: Session = Depends(get_db)) -> dict:
    """Get a single country by ID.

    Args:
        country_id: Primary key of the country.
        db: Injected DB session.

    Returns:
        Country record.

    Raises:
        HTTPException: 404 if not found.
    """
    row = db.execute(
        text("SELECT id_country, country_name FROM dim_country WHERE id_country = :cid"),
        {"cid": country_id},
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Country not found")
    return dict(row._mapping)


# ── Sports ───────────────────────────────────────────────────────

@router.get(
    "/sports",
    response_model=list[SportOut],
    tags=["dimensions"],
    dependencies=[Depends(verify_api_key)],
)
def list_sports(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[dict]:
    """List sports with pagination.

    Args:
        limit: Max records per page.
        offset: Number of records to skip.
        db: Injected DB session.

    Returns:
        List of sport records.
    """
    rows = db.execute(
        text("SELECT id_sport, sport_name_fr, sport_name_en, id_federation FROM dim_sport ORDER BY sport_name_fr LIMIT :lim OFFSET :off"),
        {"lim": limit, "off": offset},
    )
    return [dict(r._mapping) for r in rows]


# ── Federations ──────────────────────────────────────────────────

@router.get(
    "/federations",
    response_model=list[FederationOut],
    tags=["dimensions"],
    dependencies=[Depends(verify_api_key)],
)
def list_federations(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[dict]:
    """List federations with pagination.

    Args:
        limit: Max records per page.
        offset: Number of records to skip.
        db: Injected DB session.

    Returns:
        List of federation records.
    """
    rows = db.execute(
        text("SELECT id_federation, federation_name, federation_short FROM dim_federation ORDER BY federation_name LIMIT :lim OFFSET :off"),
        {"lim": limit, "off": offset},
    )
    return [dict(r._mapping) for r in rows]


# ── Editions ─────────────────────────────────────────────────────

@router.get(
    "/editions",
    response_model=list[EditionOut],
    tags=["dimensions"],
    dependencies=[Depends(verify_api_key)],
)
def list_editions(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[dict]:
    """List Olympic editions with pagination.

    Args:
        limit: Max records per page.
        offset: Number of records to skip.
        db: Injected DB session.

    Returns:
        List of edition records.
    """
    rows = db.execute(
        text(
            "SELECT id_edition, season_year, start_date, end_date, city, host_country, competition_type "
            "FROM dim_edition ORDER BY season_year DESC, city LIMIT :lim OFFSET :off"
        ),
        {"lim": limit, "off": offset},
    )
    return [dict(r._mapping) for r in rows]


# ── Results ──────────────────────────────────────────────────────

@router.get(
    "/results",
    response_model=PaginatedResults,
    tags=["results"],
    dependencies=[Depends(verify_api_key)],
)
def list_results(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    country_id: int | None = Query(default=None, description="Filter by country ID"),
    db: Session = Depends(get_db),
) -> dict:
    """List results with pagination and optional country filter.

    Args:
        page: Page number (1-based).
        page_size: Records per page.
        country_id: Optional filter by country.
        db: Injected DB session.

    Returns:
        Paginated result set.
    """
    where = "WHERE id_country = :cid" if country_id else ""
    params: dict = {"lim": page_size, "off": (page - 1) * page_size}
    if country_id:
        params["cid"] = country_id

    total_row = db.execute(text(f"SELECT COUNT(*) FROM fact_result {where}"), params).scalar()
    rows = db.execute(
        text(
            f"SELECT id_result, id_evenement, id_country, id_athlete, "
            f"athlete_last_name, athlete_first_name, id_team, team_name, "
            f"rank, performance_text, performance_value, source_id, "
            f"created_at, updated_at "
            f"FROM fact_result {where} ORDER BY id_result LIMIT :lim OFFSET :off"
        ),
        params,
    )
    return {
        "total": total_row,
        "page": page,
        "page_size": page_size,
        "items": [dict(r._mapping) for r in rows],
    }


@router.get(
    "/results/{result_id}",
    response_model=ResultDetail,
    tags=["results"],
    dependencies=[Depends(verify_api_key)],
)
def get_result(result_id: int, db: Session = Depends(get_db)) -> dict:
    """Get a single result with enriched dimension data.

    Args:
        result_id: Primary key of the result.
        db: Injected DB session.

    Returns:
        Result record with country and event names.

    Raises:
        HTTPException: 404 if not found.
    """
    row = db.execute(
        text(
            "SELECT r.*, c.country_name, ev.event_name_fr "
            "FROM fact_result r "
            "LEFT JOIN dim_country c ON r.id_country = c.id_country "
            "LEFT JOIN dim_evenement ev ON r.id_evenement = ev.id_evenement "
            "WHERE r.id_result = :rid"
        ),
        {"rid": result_id},
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Result not found")
    return dict(row._mapping)


# ── Stats ────────────────────────────────────────────────────────

@router.get(
    "/stats/results-by-country",
    response_model=list[MedalCount],
    tags=["stats"],
    dependencies=[Depends(verify_api_key)],
)
def results_by_country(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Aggregate total results per country (top N).

    Args:
        limit: Number of top countries to return.
        db: Injected DB session.

    Returns:
        List of countries with result counts, descending.
    """
    rows = db.execute(
        text(
            "SELECT c.country_name, COUNT(*) AS total_results "
            "FROM fact_result r "
            "JOIN dim_country c ON r.id_country = c.id_country "
            "GROUP BY c.country_name "
            "ORDER BY total_results DESC "
            "LIMIT :lim"
        ),
        {"lim": limit},
    )
    return [dict(r._mapping) for r in rows]
