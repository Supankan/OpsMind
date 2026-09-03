"""Incident and investigation run business service layer."""

import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from opsmind.common.errors import (
    ActiveInvestigationExistsError,
    IncidentNotFoundError,
    IncidentNotInvestigatableError,
    InvestigationNotFoundError,
)
from opsmind.common.logging import get_logger
from opsmind.common.time import utc_now
from opsmind.incidents.lifecycle import (
    ACTIVE_INVESTIGATION_STATUSES,
    is_incident_investigatable,
)
from opsmind.incidents.models import (
    Incident,
    IncidentEnvironment,
    IncidentSeverity,
    IncidentStatus,
    InvestigationRun,
    InvestigationRunStatus,
)
from opsmind.incidents.schemas import IncidentCreate

logger = get_logger(__name__)


def create_incident(session: Session, data: IncidentCreate) -> Incident:
    """Create a new operational incident.

    New incidents always begin in DETECTED status. Non-idempotent: does not
    deduplicate on external_ref.
    """
    detected_at = data.detected_at or utc_now()
    incident = Incident(
        title=data.title,
        description=data.description,
        environment=data.environment,
        severity=data.severity,
        status=IncidentStatus.DETECTED,
        service_hint=data.service_hint,
        external_ref=data.external_ref,
        detected_at=detected_at,
        trigger_payload=data.trigger_payload,
    )
    session.add(incident)
    session.commit()
    session.refresh(incident)

    logger.info(
        "Created new incident",
        incident_id=str(incident.id),
        title=incident.title,
        status=incident.status.value,
    )
    return incident


def get_incident(session: Session, incident_id: uuid.UUID) -> tuple[Incident, int]:
    """Retrieve an incident by ID along with its total count of investigation runs."""
    incident = session.get(Incident, incident_id)
    if incident is None:
        raise IncidentNotFoundError(incident_id)

    run_count_stmt = (
        select(func.count())
        .select_from(InvestigationRun)
        .where(InvestigationRun.incident_id == incident_id)
    )
    run_count = session.scalar(run_count_stmt) or 0
    return incident, run_count


def list_incidents(
    session: Session,
    limit: int = 20,
    offset: int = 0,
    status: IncidentStatus | None = None,
    environment: IncidentEnvironment | None = None,
    severity: IncidentSeverity | None = None,
) -> tuple[Sequence[Incident], int]:
    """List incidents with optional filters, deterministic ordering, and pagination."""
    base_query = select(Incident)
    count_query = select(func.count()).select_from(Incident)

    if status is not None:
        base_query = base_query.where(Incident.status == status)
        count_query = count_query.where(Incident.status == status)

    if environment is not None:
        base_query = base_query.where(Incident.environment == environment)
        count_query = count_query.where(Incident.environment == environment)

    if severity is not None:
        base_query = base_query.where(Incident.severity == severity)
        count_query = count_query.where(Incident.severity == severity)

    total = session.scalar(count_query) or 0

    # Deterministic sorting: detected_at DESC, id DESC
    paged_query = (
        base_query.order_by(Incident.detected_at.desc(), Incident.id.desc())
        .offset(offset)
        .limit(limit)
    )
    items = session.scalars(paged_query).all()
    return items, total


def register_investigation_run(session: Session, incident_id: uuid.UUID) -> InvestigationRun:
    """Register a new investigation run in PENDING status for an eligible incident.

    Guardrails:
    1. Incident must exist.
    2. Incident status must be in INVESTIGATABLE_INCIDENT_STATUSES.
    3. Incident must not already have a PENDING or RUNNING investigation run.
    4. Registering a run does NOT alter the incident status.
    """
    # Lock parent incident row with SELECT ... FOR UPDATE to serialize concurrent registrations
    incident_stmt = select(Incident).where(Incident.id == incident_id).with_for_update()
    incident = session.scalar(incident_stmt)
    if incident is None:
        raise IncidentNotFoundError(incident_id)

    if not is_incident_investigatable(incident.status):
        raise IncidentNotInvestigatableError(incident_id=incident_id, status=incident.status.value)

    active_run_stmt = select(InvestigationRun).where(
        InvestigationRun.incident_id == incident_id,
        InvestigationRun.status.in_(ACTIVE_INVESTIGATION_STATUSES),
    )
    active_run = session.scalars(active_run_stmt).first()
    if active_run is not None:
        raise ActiveInvestigationExistsError(
            incident_id=incident_id, active_run_id=str(active_run.id)
        )

    run = InvestigationRun(
        incident_id=incident_id,
        status=InvestigationRunStatus.PENDING,
        runtime_model_provider=None,
        runtime_model_name=None,
        prompt_context_version=None,
        retrieval_config={},
        budget_config={},
        code_version=None,
        started_at=None,
        finished_at=None,
    )
    session.add(run)
    session.commit()
    session.refresh(run)

    logger.info(
        "Registered new investigation run",
        run_id=str(run.id),
        incident_id=str(incident_id),
        status=run.status.value,
    )
    return run


def get_investigation_run(session: Session, run_id: uuid.UUID) -> InvestigationRun:
    """Retrieve an investigation run by ID."""
    run = session.get(InvestigationRun, run_id)
    if run is None:
        raise InvestigationNotFoundError(run_id)
    return run
