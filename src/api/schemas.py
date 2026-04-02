"""Pydantic response models for the REST API.

Maps to the target database schema defined in sql/init_target_db.sql.
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class CountryOut(BaseModel):
    """Country dimension record."""

    model_config = ConfigDict(from_attributes=True)

    id_country: int
    country_name: str


class FederationOut(BaseModel):
    """Federation dimension record."""

    model_config = ConfigDict(from_attributes=True)

    id_federation: int
    federation_name: str
    federation_short: str | None = None


class SportOut(BaseModel):
    """Sport dimension record."""

    model_config = ConfigDict(from_attributes=True)

    id_sport: int
    sport_name_fr: str
    sport_name_en: str
    id_federation: int | None = None


class EditionOut(BaseModel):
    """Olympic edition dimension record."""

    model_config = ConfigDict(from_attributes=True)

    id_edition: int
    season_year: int
    start_date: date
    end_date: date
    city: str
    host_country: str
    competition_type: str


class ResultOut(BaseModel):
    """Fact result record."""

    model_config = ConfigDict(from_attributes=True)

    id_result: int
    id_evenement: int
    id_country: int
    id_athlete: int | None = None
    athlete_last_name: str | None = None
    athlete_first_name: str | None = None
    id_team: int | None = None
    team_name: str | None = None
    rank: int | None = None
    performance_text: str | None = None
    performance_value: float | None = None
    source_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ResultDetail(ResultOut):
    """Enriched result with joined dimension names."""

    country_name: str | None = None
    event_name_fr: str | None = None


class MedalCount(BaseModel):
    """Aggregated medal count per country."""

    country_name: str
    total_results: int


class PaginatedResults(BaseModel):
    """Paginated wrapper for result lists."""

    total: int
    page: int
    page_size: int
    items: list[ResultOut]
