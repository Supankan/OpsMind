"""API routers package."""

from apps.api.routers.incidents import router as incidents_router
from apps.api.routers.investigations import router as investigations_router

__all__ = ["incidents_router", "investigations_router"]
