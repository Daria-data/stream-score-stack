"""Unit tests for normalize_columns module."""

from __future__ import annotations

import pandas as pd

from src.pipelines.transform.normalize_columns import (
    _clean_string,
    _to_snake_case,
    normalize_dataframe,
)


class TestCleanString:
    """Verify edge cases of _clean_string helper."""

    def test_strips_whitespace(self) -> None:
        assert _clean_string("  hello  ") == "hello"

    def test_null_variants_return_none(self) -> None:
        for v in (None, "null", "None", "NaN", "  nan ", ""):
            assert _clean_string(v) is None, f"Expected None for {v!r}"

    def test_normal_value_unchanged(self) -> None:
        assert _clean_string("Paris") == "Paris"


class TestToSnakeCase:
    """Verify CamelCase to snake_case conversion."""

    def test_camel(self) -> None:
        assert _to_snake_case("CountryName") == "country_name"

    def test_already_snake(self) -> None:
        assert _to_snake_case("id_sport") == "id_sport"

    def test_acronym(self) -> None:
        assert _to_snake_case("getHTTPResponse") == "get_http_response"


class TestNormalizeDataframe:
    """Verify full normalization pipeline on a mini DataFrame."""

    def test_renames_columns(self, sample_api_countries: pd.DataFrame) -> None:
        result = normalize_dataframe(sample_api_countries, "api_countries")
        assert "id_country" in result.columns
        assert "id_pays" not in result.columns

    def test_converts_booleans(self, sample_pg_epreuves: pd.DataFrame) -> None:
        result = normalize_dataframe(sample_pg_epreuves, "pg_epreuves")
        assert result["is_individual"].iloc[0] == True  # noqa: E712

    def test_integer_columns(self, sample_api_countries: pd.DataFrame) -> None:
        result = normalize_dataframe(sample_api_countries, "api_countries")
        assert pd.api.types.is_integer_dtype(result["id_country"])

    def test_unknown_source_passthrough(self) -> None:
        df = pd.DataFrame({"col_a": [1], "col_b": ["x"]})
        result = normalize_dataframe(df, "unknown_source")
        assert list(result.columns) == ["col_a", "col_b"]
