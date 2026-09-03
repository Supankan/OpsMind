"""OpsMind FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Response, status

from opsmind.common.logging import get_logger, setup_logging
from opsmind.db.session import check_db_connectivity
from opsmind.settings.config import get_settings

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Lifespan context manager for application startup and shutdown events."""
    settings = get_settings()
    setup_logging(log_level=settings.log_level, environment=settings.environment)
    logger.info(
        "Starting OpsMind API control plane",
        app_name=settings.app_name,
        environment=settings.environment,
    )
    yield
    logger.info("Shutting down OpsMind API control plane")


app = FastAPI(
    title="OpsMind API",
    description="Evidence-grounded SRE incident investigation platform",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get(
    "/health/live",
    tags=["Health"],
    summary="Liveness probe",
    description="Returns 200 OK if the application server is alive and responding.",
)
async def health_live() -> dict[str, str]:
    """Check process liveness."""
    return {"status": "ok"}


@app.get(
    "/health/ready",
    tags=["Health"],
    summary="Readiness probe",
    description="Returns 200 OK if all critical backing dependencies (PostgreSQL) are reachable.",
)
async def health_ready(response: Response) -> dict[str, Any]:
    """Check application readiness including database connectivity."""
    db_ok = check_db_connectivity()
    if not db_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "not_ready",
            "database": "disconnected",
        }

    return {
        "status": "ready",
        "database": "connected",
    }
