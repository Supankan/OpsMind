"""Integration tests for FastAPI health endpoints."""

from unittest import mock

import httpx
import pytest

from apps.api.main import app


@pytest.mark.asyncio
async def test_health_live_endpoint() -> None:
    """Verify that /health/live returns 200 OK and status ok."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health/live")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_health_ready_endpoint_connected() -> None:
    """Verify that /health/ready returns 200 OK and ready status when database is reachable."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["database"] == "connected"


@pytest.mark.asyncio
async def test_health_ready_endpoint_disconnected() -> None:
    """Verify that /health/ready returns 503 Service Unavailable when database check fails."""
    with mock.patch("apps.api.main.check_db_connectivity", return_value=False):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/health/ready")
            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "not_ready"
            assert data["database"] == "disconnected"
