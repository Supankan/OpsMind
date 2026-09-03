"""Integration tests for PostgreSQL connectivity and ORM persistence."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from opsmind.db.session import check_db_connectivity
from opsmind.incidents.models import (
    Incident,
    IncidentEnvironment,
    IncidentSeverity,
    IncidentStatus,
    InvestigationRun,
    InvestigationRunStatus,
)


def test_postgres_live_connectivity() -> None:
    """Verify that the PostgreSQL container is reachable and accepts queries."""
    assert check_db_connectivity() is True


def test_incident_and_run_persistence_lifecycle(db_session: Session) -> None:
    """Test full CRUD lifecycle for Incident and InvestigationRun in PostgreSQL."""
    # 1. Create Incident
    incident = Incident(
        external_ref="INC-1001",
        title="Payment Service Unreachable",
        description="Checkout service failing with connection refused when calling payment.",
        environment=IncidentEnvironment.DEVELOPMENT,
        severity=IncidentSeverity.CRITICAL,
        status=IncidentStatus.INVESTIGATING,
        service_hint="payment",
        trigger_payload={"metric": "http_requests_total", "code": "500"},
    )
    db_session.add(incident)
    db_session.commit()
    db_session.refresh(incident)

    assert incident.id is not None
    incident_id = incident.id

    # 2. Query Incident
    stmt = select(Incident).where(Incident.id == incident_id)
    fetched_incident = db_session.scalar(stmt)
    assert fetched_incident is not None
    assert fetched_incident.external_ref == "INC-1001"
    assert fetched_incident.status == IncidentStatus.INVESTIGATING
    assert fetched_incident.trigger_payload["code"] == "500"

    # 3. Add InvestigationRun
    run = InvestigationRun(
        incident_id=incident_id,
        status=InvestigationRunStatus.RUNNING,
        retrieval_config={"top_k": 3},
        budget_config={"max_iterations": 8},
        code_version="v0.1.0-pass01",
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)

    assert run.id is not None
    run_id = run.id

    # 4. Verify Relationship
    db_session.refresh(fetched_incident)
    assert len(fetched_incident.runs) == 1
    assert fetched_incident.runs[0].id == run_id

    # 5. Verify Cascade Deletion
    db_session.delete(fetched_incident)
    db_session.commit()

    # Verify both incident and run are deleted
    assert db_session.get(Incident, incident_id) is None
    assert db_session.get(InvestigationRun, run_id) is None
