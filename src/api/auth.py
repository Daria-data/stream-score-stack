"""API key authentication via X-API-Key header.

Simple, transparent API key authentication for development and controlled deployments.
The expected key is read from the ``API_KEY`` environment variable.

Security note:
    A hard-coded fallback (``_DEFAULT_KEY``) is provided **only** so that the
    Docker Compose stack starts without a mandatory ``.env`` file.  In a
    production deployment the variable MUST be set explicitly and the fallback
    MUST be removed.  A startup warning is emitted when the default is active.

Usage:
    @router.get("/protected", dependencies=[Depends(verify_api_key)])
"""

from __future__ import annotations

import logging
import os

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

logger = logging.getLogger(__name__)

_DEFAULT_KEY = "e4-demo-key-2026"

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
_EXPECTED_KEY: str = os.getenv("API_KEY", _DEFAULT_KEY)

if _EXPECTED_KEY == _DEFAULT_KEY:
    logger.warning(
        "API_KEY env var not set, using built-in demo key. "
        "Do NOT use in production.",
    )


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
