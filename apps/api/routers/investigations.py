"""Investigations API router."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from opsmind.db.session import get_db_session
from opsmind.incidents import service
from opsmind.incidents.schemas import InvestigationRunRead

router = APIRouter(prefix="/api/v1/investigations", tags=["Investigations"])

DbSession = Annotated[Session, Depends(get_db_session)]


@router.get(
    "/{run_id}",
    response_model=InvestigationRunRead,
    status_code=status.HTTP_200_OK,
    summary="Get an investigation run",
    description="Retrieve details and execution state of an investigation run by UUID.",
)
def get_investigation_run(
    run_id: uuid.UUID,
    db: DbSession,
) -> InvestigationRunRead:
    """Retrieve an investigation run by primary key."""
    run = service.get_investigation_run(session=db, run_id=run_id)
    return InvestigationRunRead.model_validate(run)
