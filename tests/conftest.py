"""Pytest configuration and shared test fixtures."""

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from opsmind.settings.config import Settings, get_settings


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Return test settings."""
    return get_settings()


@pytest.fixture(scope="function")
def db_session(test_settings: Settings) -> Generator[Session]:
    """Provide a transactional database session that rolls back after each test."""
    engine = create_engine(test_settings.database_url)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
