"""Unit tests for Incident and Investigation Run Pydantic schemas."""

import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from opsmind.incidents.models import (
    IncidentEnvironment,
    IncidentSeverity,
    IncidentStatus,
)
from opsmind.incidents.schemas import (
    ErrorResponse,
    IncidentCreate,
    IncidentDetailRead,
)


def test_incident_create_valid_minimal() -> None:
    """Verify IncidentCreate minimal valid instantiation."""
    schema = IncidentCreate(title="Checkout service down")
    assert schema.title == "Checkout service down"
    assert schema.description == ""
    assert schema.environment == IncidentEnvironment.DEVELOPMENT
    assert schema.severity == IncidentSeverity.MEDIUM
    assert schema.service_hint is None
    assert schema.external_ref is None
    assert schema.detected_at is None
    assert schema.trigger_payload == {}


def test_incident_create_whitespace_trimming() -> None:
    """Verify that title is stripped of leading and trailing whitespace."""
    schema = IncidentCreate(title="  Payment Latency Spike  ")
    assert schema.title == "Payment Latency Spike"


@pytest.mark.parametrize("blank_title", ["", "   ", "\t", "\n"])
def test_incident_create_blank_title_rejected(blank_title: str) -> None:
    """Verify that empty or whitespace-only titles are rejected."""
    with pytest.raises(ValidationError) as exc_info:
        IncidentCreate(title=blank_title)
    errors = exc_info.value.errors()
    assert any("title" in err["loc"] for err in errors)


def test_incident_create_forbids_status_injection() -> None:
    """Verify that client cannot set status during incident creation."""
    with pytest.raises(ValidationError) as exc_info:
        IncidentCreate(title="Valid title", status="RESOLVED")  # type: ignore[call-arg]
    errors = exc_info.value.errors()
    assert any(err["type"] == "extra_forbidden" for err in errors)


def test_incident_detail_read_run_count() -> None:
    """Verify IncidentDetailRead includes investigation_run_count."""
    now = datetime.now(UTC)
    incident_id = uuid.uuid4()
    detail = IncidentDetailRead(
        id=incident_id,
        external_ref="INC-1",
        title="Test",
        description="",
        environment=IncidentEnvironment.PRODUCTION,
        severity=IncidentSeverity.CRITICAL,
        status=IncidentStatus.DETECTED,
        service_hint="payment",
        detected_at=now,
        investigation_start=None,
        resolved_at=None,
        trigger_payload={},
        created_at=now,
        updated_at=now,
        investigation_run_count=3,
    )
    assert detail.investigation_run_count == 3
    assert detail.id == incident_id


def test_error_response_structure() -> None:
    """Verify ErrorResponse schema serializes to the approved JSON envelope."""
    payload = {
        "error": {
            "code": "INCIDENT_NOT_FOUND",
            "message": "Incident not found",
            "details": {"incident_id": "123"},
        }
    }
    error_obj = ErrorResponse.model_validate(payload)
    dumped = error_obj.model_dump()
    assert dumped["error"]["code"] == "INCIDENT_NOT_FOUND"
    assert dumped["error"]["details"]["incident_id"] == "123"
