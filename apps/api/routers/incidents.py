"""Incidents API router."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from opsmind.db.session import get_db_session
from opsmind.incidents import service
from opsmind.incidents.models import IncidentEnvironment, IncidentSeverity, IncidentStatus
from opsmind.incidents.schemas import (
    IncidentCreate,
    IncidentDetailRead,
    IncidentListResponse,
    IncidentRead,
    InvestigationRunRead,
)

router = APIRouter(prefix="/api/v1/incidents", tags=["Incidents"])

DbSession = Annotated[Session, Depends(get_db_session)]


@router.post(
    "",
    response_model=IncidentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an incident",
    description="Create a new operational incident. Status is automatically set to DETECTED.",
)
def create_incident(
    payload: IncidentCreate,
    db: DbSession,
) -> IncidentRead:
    """Create a new operational incident."""
    incident = service.create_incident(session=db, data=payload)
    return IncidentRead.model_validate(incident)


@router.get(
    "/{incident_id}",
    response_model=IncidentDetailRead,
    status_code=status.HTTP_200_OK,
    summary="Get an incident",
    description="Retrieve an incident by UUID, including its associated investigation run count.",
)
def get_incident(
    incident_id: uuid.UUID,
    db: DbSession,
) -> IncidentDetailRead:
    """Retrieve an incident by primary key."""
    incident, run_count = service.get_incident(session=db, incident_id=incident_id)
    incident_dict = IncidentRead.model_validate(incident).model_dump()
    incident_dict["investigation_run_count"] = run_count
    return IncidentDetailRead.model_validate(incident_dict)


@router.get(
    "",
    response_model=IncidentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List incidents",
    description="List incidents with pagination, filtering, and deterministic sorting (detected_at DESC, id DESC).",
)
def list_incidents(
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=100, description="Page size")] = 20,
    offset: Annotated[int, Query(ge=0, description="Page offset")] = 0,
    status_filter: Annotated[
        IncidentStatus | None, Query(alias="status", description="Filter by status")
    ] = None,
    environment: Annotated[
        IncidentEnvironment | None, Query(description="Filter by environment")
    ] = None,
    severity: Annotated[IncidentSeverity | None, Query(description="Filter by severity")] = None,
) -> IncidentListResponse:
    """List incidents matching query parameters."""
    items, total = service.list_incidents(
        session=db,
        limit=limit,
        offset=offset,
        status=status_filter,
        environment=environment,
        severity=severity,
    )
    return IncidentListResponse(
        items=[IncidentRead.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/{incident_id}/investigations",
    response_model=InvestigationRunRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register an investigation run",
    description="Register a new automated investigation run in PENDING status. Rejects if an active run exists or if the incident is closed.",
)
def register_investigation(
    incident_id: uuid.UUID,
    db: DbSession,
) -> InvestigationRunRead:
    """Register an automated investigation run for an eligible incident."""
    run = service.register_investigation_run(session=db, incident_id=incident_id)
    return InvestigationRunRead.model_validate(run)
