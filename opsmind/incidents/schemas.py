"""Pydantic schemas for Incidents and Investigation Runs."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from opsmind.incidents.models import (
    IncidentEnvironment,
    IncidentSeverity,
    IncidentStatus,
    InvestigationRunStatus,
)


class IncidentBase(BaseModel):
    """Base schema for Incident attributes."""

    title: str = Field(..., max_length=255)
    description: str = Field(default="")
    environment: IncidentEnvironment = Field(default=IncidentEnvironment.DEVELOPMENT)
    severity: IncidentSeverity = Field(default=IncidentSeverity.MEDIUM)
    service_hint: str | None = Field(default=None, max_length=255)
    external_ref: str | None = Field(default=None, max_length=255)
    trigger_payload: dict[str, Any] = Field(default_factory=dict)


class IncidentCreate(IncidentBase):
    """Schema for creating a new incident."""

    detected_at: datetime | None = None


class IncidentRead(IncidentBase):
    """Schema for reading an incident."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: IncidentStatus
    detected_at: datetime
    investigation_start: datetime | None = None
    resolved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class InvestigationRunRead(BaseModel):
    """Schema for reading an investigation run."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    incident_id: uuid.UUID
    status: InvestigationRunStatus
    runtime_model_provider: str | None = None
    runtime_model_name: str | None = None
    prompt_context_version: str | None = None
    retrieval_config: dict[str, Any] = Field(default_factory=dict)
    budget_config: dict[str, Any] = Field(default_factory=dict)
    code_version: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    stop_reason: str | None = None
    root_cause_summary: str | None = None
    failure_reason: str | None = None
    created_at: datetime
    updated_at: datetime
