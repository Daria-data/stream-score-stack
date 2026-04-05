"""Unit tests for clean_records module."""

from __future__ import annotations

import pandas as pd

from src.pipelines.transform.clean_records import (
    remove_null_critical,
    remove_duplicates,
    validate_foreign_keys,
    clean_dataframe,
)


class TestRemoveNullCritical:
    """Rows with NULL in critical columns must be dropped."""

    def test_drops_nulls(self) -> None:
        df = pd.DataFrame({"pk": [1, None, 3], "val": ["a", "b", "c"]})
        result, removed = remove_null_critical(df, ["pk"])
        assert removed == 1
        assert len(result) == 2

    def test_no_drop_when_clean(self) -> None:
        df = pd.DataFrame({"pk": [1, 2], "val": ["a", "b"]})
        result, removed = remove_null_critical(df, ["pk"])
        assert removed == 0
        assert len(result) == 2

    def test_missing_column_ignored(self) -> None:
        df = pd.DataFrame({"pk": [1]})
        result, removed = remove_null_critical(df, ["nonexistent"])
        assert removed == 0


class TestRemoveDuplicates:
    """Deduplication keeps first occurrence."""

    def test_dedup(self) -> None:
        df = pd.DataFrame({"pk": [1, 1, 2], "val": ["a", "b", "c"]})
        result, removed = remove_duplicates(df, "pk")
        assert removed == 1
        assert result.iloc[0]["val"] == "a"

    def test_missing_key_noop(self) -> None:
        df = pd.DataFrame({"pk": [1]})
        result, removed = remove_duplicates(df, "nonexistent")
        assert removed == 0


class TestValidateForeignKeys:
    """Rows referencing unknown FKs must be removed."""

    def test_removes_invalid(self) -> None:
        df = pd.DataFrame({"fk": [1, 2, 999]})
        result, removed = validate_foreign_keys(df, "fk", {1, 2})
        assert removed == 1
        assert 999 not in result["fk"].values

    def test_keeps_nulls(self) -> None:
        df = pd.DataFrame({"fk": [1, None]})
        result, removed = validate_foreign_keys(df, "fk", {1})
        assert removed == 0
        assert len(result) == 2


class TestCleanDataframe:
    """Integration of all cleaning steps."""

    def test_full_cleaning_pipeline(self) -> None:
        df = pd.DataFrame({
            "id_country": pd.array([1, 1, None, 3], dtype="Int64"),
            "country_name": ["France", "France dup", None, "Japan"],
        })
        result, stats = clean_dataframe(df, "api_countries")
        assert stats["null_removed"] >= 1
        assert stats["duplicates_removed"] >= 1
        assert stats["final"] < stats["initial"]
