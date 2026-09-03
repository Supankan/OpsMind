"""Integration tests for the Incident & Investigation Control Plane API."""

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import httpx
import pytest
from sqlalchemy.orm import Session

from apps.api.main import app
from opsmind.incidents.models import (
    Incident,
    IncidentEnvironment,
    IncidentSeverity,
    IncidentStatus,
    InvestigationRun,
    InvestigationRunStatus,
)


@pytest.fixture
async def async_client() -> AsyncGenerator[httpx.AsyncClient]:
    """Provide an async test client against the FastAPI application."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_create_incident_success(
    async_client: httpx.AsyncClient, db_session: Session
) -> None:
    """Test 1 & 2: Incident create -> 201 and initial status is DETECTED."""
    payload = {
        "title": "Frontend High 5xx Rates",
        "description": "Observed 15% HTTP 500 error rate on checkout route.",
        "environment": "production",
        "severity": "high",
        "service_hint": "frontend",
        "external_ref": "ALERT-5501",
        "trigger_payload": {"metric": "http_errors", "rate": 0.15},
    }
    response = await async_client.post("/api/v1/incidents", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert data["title"] == "Frontend High 5xx Rates"
    assert data["status"] == "DETECTED"
    assert data["environment"] == "production"
    assert data["severity"] == "high"
    assert data["service_hint"] == "frontend"
    assert data["external_ref"] == "ALERT-5501"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data

    # Cleanup
    created_id = uuid.UUID(data["id"])
    inc = db_session.get(Incident, created_id)
    if inc:
        db_session.delete(inc)
        db_session.commit()


@pytest.mark.asyncio
async def test_get_incident_success(async_client: httpx.AsyncClient, db_session: Session) -> None:
    """Test 3: Get incident -> returns full details and investigation_run_count."""
    incident = Incident(
        title="Payment Service Latency Spike",
        environment=IncidentEnvironment.STAGING,
        severity=IncidentSeverity.MEDIUM,
    )
    db_session.add(incident)
    db_session.commit()
    db_session.refresh(incident)

    # Add two runs
    run1 = InvestigationRun(incident_id=incident.id, status=InvestigationRunStatus.COMPLETED)
    run2 = InvestigationRun(incident_id=incident.id, status=InvestigationRunStatus.PENDING)
    db_session.add_all([run1, run2])
    db_session.commit()

    response = await async_client.get(f"/api/v1/incidents/{incident.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(incident.id)
    assert data["title"] == "Payment Service Latency Spike"
    assert data["investigation_run_count"] == 2

    # Cleanup
    db_session.delete(incident)
    db_session.commit()


@pytest.mark.asyncio
async def test_get_incident_missing(async_client: httpx.AsyncClient) -> None:
    """Test 4: Missing incident -> 404 with code INCIDENT_NOT_FOUND."""
    missing_id = uuid.uuid4()
    response = await async_client.get(f"/api/v1/incidents/{missing_id}")
    assert response.status_code == 404
    body = response.json()
    assert "error" in body
    assert body["error"]["code"] == "INCIDENT_NOT_FOUND"
    assert str(missing_id) in body["error"]["message"]


@pytest.mark.asyncio
async def test_list_incidents_pagination(
    async_client: httpx.AsyncClient, db_session: Session
) -> None:
    """Test 5: Incident list pagination (limit, offset, total)."""
    # Create 5 test incidents
    created_incidents = []
    for i in range(5):
        inc = Incident(
            title=f"Pagination Test Incident {i}",
            environment=IncidentEnvironment.TESTING,
            detected_at=datetime(2026, 9, 3, 10, i, 0, tzinfo=UTC),
        )
        db_session.add(inc)
        created_incidents.append(inc)
    db_session.commit()

    # Query with limit=2, offset=1 filtered by TESTING environment
    response = await async_client.get("/api/v1/incidents?environment=testing&limit=2&offset=1")
    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 2
    assert data["offset"] == 1
    assert data["total"] >= 5
    assert len(data["items"]) == 2

    # Cleanup
    for inc in created_incidents:
        db_session.delete(inc)
    db_session.commit()


@pytest.mark.asyncio
async def test_list_incidents_filters(async_client: httpx.AsyncClient, db_session: Session) -> None:
    """Test 6, 7 & 8: Filtering by status, environment, and severity."""
    inc1 = Incident(
        title="Filter Test Production Critical",
        environment=IncidentEnvironment.PRODUCTION,
        severity=IncidentSeverity.CRITICAL,
        status=IncidentStatus.INVESTIGATING,
    )
    inc2 = Incident(
        title="Filter Test Staging Low",
        environment=IncidentEnvironment.STAGING,
        severity=IncidentSeverity.LOW,
        status=IncidentStatus.DETECTED,
    )
    db_session.add_all([inc1, inc2])
    db_session.commit()

    # Filter status=INVESTIGATING
    resp_status = await async_client.get("/api/v1/incidents?status=INVESTIGATING")
    assert resp_status.status_code == 200
    assert all(item["status"] == "INVESTIGATING" for item in resp_status.json()["items"])

    # Filter environment=production
    resp_env = await async_client.get("/api/v1/incidents?environment=production")
    assert resp_env.status_code == 200
    assert all(item["environment"] == "production" for item in resp_env.json()["items"])

    # Filter severity=critical
    resp_sev = await async_client.get("/api/v1/incidents?severity=critical")
    assert resp_sev.status_code == 200
    assert all(item["severity"] == "critical" for item in resp_sev.json()["items"])

    # Cleanup
    db_session.delete(inc1)
    db_session.delete(inc2)
    db_session.commit()


@pytest.mark.asyncio
async def test_list_incidents_deterministic_ordering(
    async_client: httpx.AsyncClient, db_session: Session
) -> None:
    """Test 9: Stable ordering (detected_at DESC, id DESC)."""
    same_time = datetime(2026, 9, 3, 12, 0, 0, tzinfo=UTC)
    id1 = uuid.UUID("11111111-1111-1111-1111-111111111111")
    id2 = uuid.UUID("22222222-2222-2222-2222-222222222222")

    inc1 = Incident(
        id=id1,
        title="Ordering Inc 1",
        environment=IncidentEnvironment.TESTING,
        detected_at=same_time,
    )
    inc2 = Incident(
        id=id2,
        title="Ordering Inc 2",
        environment=IncidentEnvironment.TESTING,
        detected_at=same_time,
    )
    db_session.add_all([inc1, inc2])
    db_session.commit()

    response = await async_client.get("/api/v1/incidents?environment=testing")
    assert response.status_code == 200
    items = response.json()["items"]

    # Filter only our two test incidents
    test_items = [item for item in items if item["id"] in [str(id1), str(id2)]]
    assert len(test_items) == 2
    # id2 > id1, so id2 must appear before id1 when detected_at is equal
    assert test_items[0]["id"] == str(id2)
    assert test_items[1]["id"] == str(id1)

    # Cleanup
    db_session.delete(inc1)
    db_session.delete(inc2)
    db_session.commit()


@pytest.mark.asyncio
async def test_register_investigation_run_success(
    async_client: httpx.AsyncClient, db_session: Session
) -> None:
    """Test 10 & 11: Register run -> 201 PENDING and does not change incident status."""
    incident = Incident(
        title="Cart Service CrashLoop",
        status=IncidentStatus.DETECTED,
    )
    db_session.add(incident)
    db_session.commit()
    db_session.refresh(incident)

    response = await async_client.post(f"/api/v1/incidents/{incident.id}/investigations")
    assert response.status_code == 201
    run_data = response.json()
    assert run_data["status"] == "PENDING"
    assert run_data["incident_id"] == str(incident.id)
    assert run_data["runtime_model_provider"] is None

    # Verify incident status is still DETECTED
    db_session.refresh(incident)
    assert incident.status == IncidentStatus.DETECTED

    # Cleanup
    db_session.delete(incident)
    db_session.commit()


@pytest.mark.asyncio
async def test_register_investigation_duplicate_active_rejected(
    async_client: httpx.AsyncClient, db_session: Session
) -> None:
    """Test 12: Duplicate active run -> 409 ACTIVE_INVESTIGATION_EXISTS."""
    incident = Incident(
        title="Checkout Latency",
        status=IncidentStatus.INVESTIGATING,
    )
    db_session.add(incident)
    db_session.commit()

    # First run in PENDING status
    run1 = InvestigationRun(incident_id=incident.id, status=InvestigationRunStatus.PENDING)
    db_session.add(run1)
    db_session.commit()

    # Attempt to register second run
    response = await async_client.post(f"/api/v1/incidents/{incident.id}/investigations")
    assert response.status_code == 409
    body = response.json()
    assert body["error"]["code"] == "ACTIVE_INVESTIGATION_EXISTS"
    assert str(run1.id) in body["error"]["message"]

    # Cleanup
    db_session.delete(incident)
    db_session.commit()


@pytest.mark.asyncio
async def test_register_investigation_ineligible_incident_rejected(
    async_client: httpx.AsyncClient, db_session: Session
) -> None:
    """Test 13: Ineligible incident -> 409 INCIDENT_NOT_INVESTIGATABLE."""
    incident = Incident(
        title="Resolved Payment Failure",
        status=IncidentStatus.RESOLVED,
    )
    db_session.add(incident)
    db_session.commit()

    response = await async_client.post(f"/api/v1/incidents/{incident.id}/investigations")
    assert response.status_code == 409
    body = response.json()
    assert body["error"]["code"] == "INCIDENT_NOT_INVESTIGATABLE"
    assert "RESOLVED" in body["error"]["message"]

    # Cleanup
    db_session.delete(incident)
    db_session.commit()


@pytest.mark.asyncio
async def test_get_investigation_run_success(
    async_client: httpx.AsyncClient, db_session: Session
) -> None:
    """Test 14: Get investigation run -> returns full run data."""
    incident = Incident(title="Ad Service High Memory")
    db_session.add(incident)
    db_session.commit()

    run = InvestigationRun(
        incident_id=incident.id,
        status=InvestigationRunStatus.RUNNING,
        code_version="v0.2.0",
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)

    response = await async_client.get(f"/api/v1/investigations/{run.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(run.id)
    assert data["incident_id"] == str(incident.id)
    assert data["status"] == "RUNNING"
    assert data["code_version"] == "v0.2.0"

    # Cleanup
    db_session.delete(incident)
    db_session.commit()


@pytest.mark.asyncio
async def test_get_investigation_run_missing(async_client: httpx.AsyncClient) -> None:
    """Test 15: Missing investigation run -> 404 INVESTIGATION_NOT_FOUND."""
    missing_id = uuid.uuid4()
    response = await async_client.get(f"/api/v1/investigations/{missing_id}")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "INVESTIGATION_NOT_FOUND"


@pytest.mark.asyncio
async def test_malformed_uuid_validation_error(async_client: httpx.AsyncClient) -> None:
    """Test 16: Malformed UUID -> 422 with code VALIDATION_ERROR."""
    response = await async_client.get("/api/v1/incidents/not-a-valid-uuid")
    assert response.status_code == 422
    body = response.json()
    assert "error" in body
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "errors" in body["error"]["details"]


@pytest.mark.asyncio
async def test_validation_error_envelope_on_blank_title(
    async_client: httpx.AsyncClient,
) -> None:
    """Test 17: Invalid payload (blank title) -> 422 with standardized error envelope."""
    response = await async_client.post(
        "/api/v1/incidents",
        json={"title": "   ", "severity": "low"},
    )
    assert response.status_code == 422
    body = response.json()
    assert "error" in body
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["message"] == "Request validation failed."
    assert "errors" in body["error"]["details"]
