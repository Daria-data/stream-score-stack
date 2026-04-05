"""FastAPI application for the Olympic Results REST API.

FastAPI service exposing the normalized Olympic results over REST.
Auto-generates OpenAPI documentation at /docs.

Usage (local):
    uvicorn src.api.main:app --host 0.0.0.0 --port 8888

Usage (Docker):
    Runs as the 'api' service in docker-compose.yml on port 8888.
"""

from __future__ import annotations

from fastapi import FastAPI

from src.api.routes import router

app = FastAPI(
    title="Olympic Results API",
    description=(
        "REST API providing access to the normalized Olympic results database.\n\n"
        "**Authentication**: all data endpoints require an `X-API-Key` header.\n\n"
        "Default demo key: `e4-demo-key-2026`"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(router)
