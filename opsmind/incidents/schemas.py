"""Pydantic schemas for Incidents and Investigation Runs."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from opsmind.incidents.models import (
    IncidentEnvironment,
    IncidentSeverity,
    IncidentStatus,
    InvestigationRunStatus,
)


class IncidentCreate(BaseModel):
    """Schema for creating a new incident.

    Status cannot be set by the client; every new incident begins in DETECTED status.
    """

    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., max_length=255, description="Short incident summary")
    description: str = Field(default="", description="Detailed incident description")
    environment: IncidentEnvironment = Field(
        default=IncidentEnvironment.DEVELOPMENT, description="Target deployment environment"
    )
    severity: IncidentSeverity = Field(
        default=IncidentSeverity.MEDIUM, description="Incident severity level"
    )
    service_hint: str | None = Field(
        default=None, max_length=255, description="Optional suspected service hint"
    )
    external_ref: str | None = Field(
        default=None, max_length=255, description="Optional external ticketing/alert ID"
    )
    detected_at: datetime | None = Field(
        default=None, description="Timestamp when incident was detected (defaults to UTC now)"
    )
    trigger_payload: dict[str, Any] = Field(
        default_factory=dict, description="Raw trigger or alert payload"
    )

    @field_validator("title")
    @classmethod
    def validate_title_not_blank(cls, v: str) -> str:
        """Ensure title is not empty or whitespace-only."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("title cannot be empty or whitespace-only")
        return stripped


class IncidentRead(BaseModel):
    """Schema for reading an incident."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    external_ref: str | None
    title: str
    description: str
    environment: IncidentEnvironment
    severity: IncidentSeverity
    status: IncidentStatus
    service_hint: str | None
    detected_at: datetime
    investigation_start: datetime | None
    resolved_at: datetime | None
    trigger_payload: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class IncidentDetailRead(IncidentRead):
    """Schema for reading detailed incident data including investigation run count."""

    investigation_run_count: int = 0


class IncidentListResponse(BaseModel):
    """Paginated incident list response envelope."""

    items: list[IncidentRead]
    total: int
    limit: int
    offset: int


class InvestigationRunRead(BaseModel):
    """Schema for reading an investigation run."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    incident_id: uuid.UUID
    status: InvestigationRunStatus
    runtime_model_provider: str | None
    runtime_model_name: str | None
    prompt_context_version: str | None
    retrieval_config: dict[str, Any]
    budget_config: dict[str, Any]
    code_version: str | None
    started_at: datetime | None
    finished_at: datetime | None
    stop_reason: str | None
    root_cause_summary: str | None
    failure_reason: str | None
    created_at: datetime
    updated_at: datetime


class ErrorDetail(BaseModel):
    """Structured error payload details."""

    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Standardized top-level error response envelope."""

    error: ErrorDetail
