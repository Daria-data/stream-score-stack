"""API key authentication via X-API-Key header.

Simple, transparent auth mechanism suitable for E4 demonstration.
The expected key is read from the API_KEY environment variable.

Usage:
    @router.get("/protected", dependencies=[Depends(verify_api_key)])
"""

from __future__ import annotations

import os

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
_EXPECTED_KEY: str = os.getenv("API_KEY", "e4-demo-key-2026")


async def verify_api_key(
    api_key: str | None = Security(API_KEY_HEADER),
) -> str:
    """Validate the API key from the request header.

    Args:
        api_key: Value from the X-API-Key header.

    Returns:
        The validated API key string.

    Raises:
        HTTPException: 401 if key is missing, 403 if key is invalid.
    """
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
        )
    if api_key != _EXPECTED_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )
    return api_key
