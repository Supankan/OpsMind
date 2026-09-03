"""Unit tests for Incident and InvestigationRun domain models."""

import uuid

from opsmind.incidents.models import (
    Incident,
    IncidentEnvironment,
    IncidentSeverity,
    IncidentStatus,
    InvestigationRun,
    InvestigationRunStatus,
)


def test_incident_instantiation() -> None:
    """Test instantiating an Incident with defaults and custom attributes."""
    incident = Incident(
        title="Payment Service Degradation",
        description="Checkout latency elevated and 503 errors observed.",
        environment=IncidentEnvironment.PRODUCTION,
        severity=IncidentSeverity.HIGH,
        service_hint="payment",
        trigger_payload={"source": "alertmanager", "alert_name": "High5xxRate"},
    )

    assert incident.title == "Payment Service Degradation"
    assert incident.environment == IncidentEnvironment.PRODUCTION
    assert incident.severity == IncidentSeverity.HIGH
    assert incident.status == IncidentStatus.DETECTED
    assert incident.service_hint == "payment"
    assert incident.trigger_payload["alert_name"] == "High5xxRate"
    assert "Payment Service Degradation" in repr(incident)


def test_investigation_run_instantiation() -> None:
    """Test instantiating an InvestigationRun with configuration payloads."""
    incident_id = uuid.uuid4()
    run = InvestigationRun(
        incident_id=incident_id,
        status=InvestigationRunStatus.RUNNING,
        retrieval_config={"top_k": 5, "mode": "dense"},
        budget_config={"max_iterations": 8},
        code_version="v0.1.0",
    )

    assert run.incident_id == incident_id
    assert run.status == InvestigationRunStatus.RUNNING
    assert run.retrieval_config["top_k"] == 5
    assert run.budget_config["max_iterations"] == 8
    assert run.code_version == "v0.1.0"
    assert run.runtime_model_provider is None
    assert str(incident_id) in repr(run)


def test_incident_investigation_run_relationship() -> None:
    """Test parent-child relationship between Incident and InvestigationRun."""
    incident = Incident(
        title="Checkout Service Timeout",
        description="Downstream payment calls timing out.",
    )
    run1 = InvestigationRun(
        incident=incident,
        status=InvestigationRunStatus.COMPLETED,
    )
    run2 = InvestigationRun(
        incident=incident,
        status=InvestigationRunStatus.PENDING,
    )

    assert len(incident.runs) == 2
    assert run1.incident is incident
    assert run2.incident is incident
    assert run1 in incident.runs
    assert run2 in incident.runs
