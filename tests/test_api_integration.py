"""Integration tests for the FastAPI application.

Uses the FastAPI TestClient (no real DB needed; we patch get_db).
"""

from __future__ import annotations

from collections.abc import Generator, Iterator
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from src.api.auth import _EXPECTED_KEY
from src.api.main import app
from src.api.db import get_db


class _FakeResult:
    """Simulate SQLAlchemy CursorResult for mocked queries."""

    def __init__(self) -> None:
        self._rows: list[Any] = []

    def __iter__(self) -> Iterator[Any]:
        return iter(self._rows)

    def scalar(self) -> int:
        return 0


def _mock_db() -> Generator[MagicMock, Any, None]:
    """Yield a mock DB session that returns empty result sets."""
    mock_session = MagicMock()
    mock_session.execute.return_value = _FakeResult()
    yield mock_session


@pytest.fixture()
def client() -> Iterator[TestClient]:
    """TestClient with DB dependency overridden."""
    app.dependency_overrides[get_db] = _mock_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


class TestHealthEndpoint:
    """Public health check requires no auth."""

    def test_health_ok(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"


class TestAuthProtection:
    """Protected endpoints enforce API key."""

    def test_no_key_returns_401(self, client: TestClient) -> None:
        resp = client.get("/countries")
        assert resp.status_code == 401

    def test_wrong_key_returns_403(self, client: TestClient) -> None:
        resp = client.get("/countries", headers={"X-API-Key": "bad"})
        assert resp.status_code == 403

    def test_valid_key_accepted(self, client: TestClient) -> None:
        resp = client.get("/countries", headers={"X-API-Key": _EXPECTED_KEY})
        assert resp.status_code == 200


class TestEndpoints:
    """Smoke tests: protected endpoints respond 200 with valid key."""

    HEADERS = {"X-API-Key": _EXPECTED_KEY}

    @pytest.mark.parametrize("path", [
        "/sports",
        "/federations",
        "/editions",
    ])
    def test_dimension_endpoints(self, client: TestClient, path: str) -> None:
        resp = client.get(path, headers=self.HEADERS)
        assert resp.status_code == 200
