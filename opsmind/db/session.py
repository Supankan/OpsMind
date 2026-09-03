"""SQLAlchemy database engine and session management."""

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from opsmind.common.logging import get_logger
from opsmind.settings.config import get_settings

logger = get_logger(__name__)


@lru_cache
def get_engine() -> Engine:
    """Create and cache the SQLAlchemy database engine."""
    settings = get_settings()
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    """Create and cache the session factory."""
    engine = get_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session() -> Generator[Session]:
    """Provide a transactional database session for FastAPI dependencies."""
    session_factory = get_session_factory()
    session: Session = session_factory()
    try:
        yield session
    finally:
        session.close()


def check_db_connectivity() -> bool:
    """Check if the database is reachable by executing a simple query."""
    engine = get_engine()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.warning("Database connectivity check failed", error=str(exc))
        return False
