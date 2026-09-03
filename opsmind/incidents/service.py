"""Incident service layer stub.

Full business logic for incidents and investigation runs will be implemented
in future passes.
"""

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from opsmind.incidents.models import Incident, InvestigationRun


def get_incident_by_id(session: Session, incident_id: uuid.UUID) -> Incident | None:
    """Retrieve an incident by primary key."""
    return session.get(Incident, incident_id)


def list_incidents(session: Session, limit: int = 50, offset: int = 0) -> Sequence[Incident]:
    """List incidents ordered by creation time descending."""
    stmt = select(Incident).order_by(Incident.created_at.desc()).limit(limit).offset(offset)
    return session.scalars(stmt).all()


def get_investigation_run(session: Session, run_id: uuid.UUID) -> InvestigationRun | None:
    """Retrieve an investigation run by primary key."""
    return session.get(InvestigationRun, run_id)
