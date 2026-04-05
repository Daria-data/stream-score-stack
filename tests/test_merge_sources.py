"""Unit tests for merge_sources module: cross-source reconciliation."""

from __future__ import annotations

import pandas as pd

from src.pipelines.transform.merge_sources import (
    merge_countries,
    merge_disciplines,
    merge_editions,
    merge_epreuves,
    merge_federations,
    merge_results,
    merge_sports,
)


def _cleaned_set() -> dict[str, pd.DataFrame]:
    """Build a small synthetic cleaned-data dict for merge tests."""
    return {
        "api_countries": pd.DataFrame({
            "id_country": pd.array([1, 2], dtype="Int64"),
            "country_name": ["France", "Germany"],
        }),
        "api_sports": pd.DataFrame({
            "id_sport": pd.array([37], dtype="Int64"),
            "sport_name_fr": ["Athlétisme"],
            "sport_name_en": ["Athletics"],
            "id_federation": pd.array([5], dtype="Int64"),
            "federation_name": ["World Athletics"],
            "federation_short": ["WA"],
        }),
        "pg_epreuves": pd.DataFrame({
            "id_epreuve": pd.array([10, 20], dtype="Int64"),
            "epreuve_name": ["100m", "Marathon"],
            "genre": ["Hommes", "Femmes"],
            "epreuve_type": ["Individuel", "Individuel"],
            "is_individual": [True, True],
            "is_olympic": [True, True],
            "is_summer": [True, True],
            "is_handicap": [False, False],
            "result_direction": pd.array([0, 0], dtype="Int64"),
            "id_discipline": pd.array([251, 251], dtype="Int64"),
            "discipline_name": ["Athlétisme", "Athlétisme"],
            "id_sport": pd.array([37, 37], dtype="Int64"),
        }),
        "parquet_federations": pd.DataFrame({
            "id_federation": pd.array([5, 99], dtype="Int64"),
            "federation_name": ["World Athletics", "Extra Fed"],
            "federation_short": ["WA", "EF"],
        }),
        "file_results": pd.DataFrame({
            "id_result": pd.array([100, 200, 300], dtype="Int64"),
            "source_id": [None, None, None],
            "data_source": ["file", "file", "file"],
            "id_athlete": pd.array([1, 2, 3], dtype="Int64"),
            "id_person": [None, None, None],
            "athlete_last_name": ["Bolt", "Kipchoge", "Ghost"],
            "athlete_first_name": ["Usain", "Eliud", "X"],
            "id_team": [None, None, None],
            "team_name": [None, None, None],
            "id_country": pd.array([1, 2, 999], dtype="Int64"),
            "id_epreuve": pd.array([10, 20, 10], dtype="Int64"),
            "id_evenement": pd.array([500, 600, 500], dtype="Int64"),
            "id_edition": pd.array([1, 1, 1], dtype="Int64"),
            "rank": pd.array([1, 1, None], dtype="Int64"),
            "performance_text": ["9.58", "2:01:39", None],
            "performance_value": [9.58, 7299.0, None],
            "created_at": [None, None, None],
            "updated_at": [None, None, None],
        }),
        "html_editions": pd.DataFrame({
            "id_edition": pd.array([1, 5, 9], dtype="Int64"),
            "season_year": [2024, 2024, 2020],
            "start_date": ["2024-07-26", "2024-07-26", "2021-07-23"],
            "end_date": ["2024-08-11", "2024-08-11", "2021-08-08"],
            "city": ["Paris", "Paris", "Tokyo"],
            "host_country": ["France", "France", "Japan"],
            "competition_type": ["JO été", "JO été", "JO été"],
        }),
        "pg_evenements": pd.DataFrame({
            "id_evenement": pd.array([500, 600, 700], dtype="Int64"),
            "event_name_fr": ["100m H Paris", "Marathon F Paris", "100m H Tokyo"],
            "event_name_en": ["100m M Paris", "Marathon W Paris", "100m M Tokyo"],
            "age_category": [None, None, None],
            "id_epreuve": pd.array([10, 20, 10], dtype="Int64"),
            "id_edition": pd.array([1, 5, 9], dtype="Int64"),
        }),
    }


class TestMergeCountries:
    """Countries: API is reference, cross-check with results."""

    def test_returns_api_countries(self) -> None:
        result = merge_countries(_cleaned_set())
        assert len(result) == 2
        assert set(result["country_name"]) == {"France", "Germany"}

    def test_empty_when_no_source(self) -> None:
        assert merge_countries({}).empty


class TestMergeSports:
    """Sports: API catalog, cross-check with épreuves."""

    def test_returns_api_sports(self) -> None:
        result = merge_sports(_cleaned_set())
        assert len(result) == 1
        assert result.iloc[0]["sport_name_en"] == "Athletics"


class TestMergeDisciplines:
    """Disciplines: extracted from épreuves, deduplicated."""

    def test_deduplicates(self) -> None:
        result = merge_disciplines(_cleaned_set())
        assert len(result) == 1
        assert result.iloc[0]["discipline_name"] == "Athlétisme"


class TestMergeEpreuves:
    """Épreuves carry id_sport for the FK constraint."""

    def test_id_sport_present(self) -> None:
        result = merge_epreuves(_cleaned_set())
        assert "id_sport" in result.columns
        assert result["id_sport"].notna().all()


class TestMergeFederations:
    """Federations: API + Parquet, dedup by id_federation."""

    def test_deduplicates_across_sources(self) -> None:
        result = merge_federations(_cleaned_set())
        assert len(result) == 2
        ids = set(result["id_federation"])
        assert ids == {5, 99}


class TestMergeEditions:
    """Editions: deduplicate by business key, canonical id."""

    def test_deduplicates_by_business_key(self) -> None:
        df, id_map = merge_editions(_cleaned_set())
        assert len(df) == 2, "Paris 2024 (ids 1 & 5) must collapse into 1 row"
        assert 1 in df["id_edition"].values, "MIN id (1) is the canonical PK"
        assert 5 not in df["id_edition"].values, "Duplicate id (5) must be removed"

    def test_returns_remap_dict(self) -> None:
        _, id_map = merge_editions(_cleaned_set())
        assert id_map == {5: 1}, "Old id 5 must map to canonical 1"

    def test_keeps_all_unique_games(self) -> None:
        df, _ = merge_editions(_cleaned_set())
        cities = set(df["city"])
        assert cities == {"Paris", "Tokyo"}


class TestMergeResults:
    """Results FK validation drops rows with unknown country."""

    def test_drops_invalid_country(self) -> None:
        result = merge_results(_cleaned_set())
        assert 999 not in result["id_country"].values
        assert len(result) == 2

    def test_keeps_valid_rows(self) -> None:
        result = merge_results(_cleaned_set())
        assert set(result["id_country"]) == {1, 2}
