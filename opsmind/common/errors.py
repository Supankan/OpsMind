"""Common domain error definitions."""

from typing import Any


class OpsMindError(Exception):
    """Base exception for all OpsMind domain errors."""

    code: str = "INTERNAL_ERROR"
    status_code: int = 500

    def __init__(
        self,
        message: str,
        code: str | None = None,
        details: dict[str, Any] | None = None,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        self.details = details or {}


class DatabaseError(OpsMindError):
    """Raised when a database operation fails."""

    code = "DATABASE_ERROR"
    status_code = 500


class EntityNotFoundError(OpsMindError):
    """Raised when a requested domain entity cannot be found."""

    code = "ENTITY_NOT_FOUND"
    status_code = 404


class IncidentNotFoundError(EntityNotFoundError):
    """Raised when an incident is not found by ID."""

    code = "INCIDENT_NOT_FOUND"
    status_code = 404

    def __init__(self, incident_id: Any, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=f"Incident {incident_id} was not found.",
            code=self.code,
            details=details,
            status_code=self.status_code,
        )


class InvestigationNotFoundError(EntityNotFoundError):
    """Raised when an investigation run is not found by ID."""

    code = "INVESTIGATION_NOT_FOUND"
    status_code = 404

    def __init__(self, run_id: Any, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=f"Investigation run {run_id} was not found.",
            code=self.code,
            details=details,
            status_code=self.status_code,
        )


class IncidentNotInvestigatableError(OpsMindError):
    """Raised when attempting to register an investigation on an ineligible incident."""

    code = "INCIDENT_NOT_INVESTIGATABLE"
    status_code = 409

    def __init__(
        self, incident_id: Any, status: str, details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(
            message=f"Incident {incident_id} in status '{status}' is not eligible for investigation.",
            code=self.code,
            details=details,
            status_code=self.status_code,
        )


class ActiveInvestigationExistsError(OpsMindError):
    """Raised when an incident already has an active (PENDING or RUNNING) investigation run."""

    code = "ACTIVE_INVESTIGATION_EXISTS"
    status_code = 409

    def __init__(
        self, incident_id: Any, active_run_id: Any, details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(
            message=(
                f"Incident {incident_id} already has an active investigation run ({active_run_id})."
            ),
            code=self.code,
            details=details,
            status_code=self.status_code,
        )


class ValidationError(OpsMindError):
    """Raised when entity data fails domain validation."""

    code = "VALIDATION_ERROR"
    status_code = 422
