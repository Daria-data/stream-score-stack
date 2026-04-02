"""Database session management for the REST API.

Provides a SQLAlchemy engine and a dependency-injectable session generator
for FastAPI route handlers.

Environment variables:
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
"""

from __future__ import annotations

import os
from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


def _build_url() -> str:
    """Construct PostgreSQL connection URL from environment.

    Returns:
        SQLAlchemy-compatible connection string.
    """
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5433")
    name = os.getenv("DB_NAME", "sports")
    user = os.getenv("DB_USER", "postgres")
    pwd = os.getenv("DB_PASSWORD", "postgres")
    return f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{name}"


engine: Engine = create_engine(_build_url(), pool_pre_ping=True)
SessionLocal: sessionmaker[Session] = sessionmaker(bind=engine, expire_on_commit=False)


def get_db() -> Generator[Session, Any, None]:
    """Yield a DB session and ensure cleanup.

    Yields:
        Active SQLAlchemy session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
