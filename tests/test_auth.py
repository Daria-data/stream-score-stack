"""Unit tests for API key authentication."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from src.api.auth import verify_api_key, _EXPECTED_KEY


class TestVerifyApiKey:
    """Verify the three auth outcomes: success, missing, invalid."""

    @pytest.mark.asyncio
    async def test_valid_key_returns_key(self) -> None:
        result = await verify_api_key(_EXPECTED_KEY)
        assert result == _EXPECTED_KEY

    @pytest.mark.asyncio
    async def test_missing_key_raises_401(self) -> None:
        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key(None)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_key_raises_403(self) -> None:
        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key("wrong-key")
        assert exc_info.value.status_code == 403
