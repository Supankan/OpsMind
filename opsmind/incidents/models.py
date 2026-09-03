"""SQLAlchemy models for Incidents and Investigation Runs."""

import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, Uuid, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from opsmind.common.time import utc_now
from opsmind.db.base import Base


class IncidentEnvironment(enum.StrEnum):
    """Target deployment environment of an incident."""

    PRODUCTION = "production"
    STAGING = "staging"
    DEVELOPMENT = "development"
    TESTING = "testing"


class IncidentSeverity(enum.StrEnum):
    """Incident severity classification."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IncidentStatus(enum.StrEnum):
    """Operational lifecycle status of an incident."""

    DETECTED = "DETECTED"
    TRIAGING = "TRIAGING"
    INVESTIGATING = "INVESTIGATING"
    ROOT_CAUSE_PROPOSED = "ROOT_CAUSE_PROPOSED"
    REMEDIATION_PROPOSED = "REMEDIATION_PROPOSED"
    RESOLVED = "RESOLVED"
    POSTMORTEM_COMPLETE = "POSTMORTEM_COMPLETE"
    INVESTIGATION_FAILED = "INVESTIGATION_FAILED"
    INCONCLUSIVE = "INCONCLUSIVE"
    CANCELLED = "CANCELLED"


class InvestigationRunStatus(enum.StrEnum):
    """Execution status of an investigation run."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    INCONCLUSIVE = "INCONCLUSIVE"
    CANCELLED = "CANCELLED"


# JSON column type supporting both PostgreSQL JSONB and SQLite JSON
JSON_TYPE = JSONB().with_variant(JSON, "sqlite")


class Incident(Base):
    """Represents an operational incident or alert under investigation."""

    __tablename__ = "incidents"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    external_ref: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )
    environment: Mapped[IncidentEnvironment] = mapped_column(
        SAEnum(IncidentEnvironment, name="incident_environment_enum", native_enum=False),
        nullable=False,
        default=IncidentEnvironment.DEVELOPMENT,
    )
    severity: Mapped[IncidentSeverity] = mapped_column(
        SAEnum(IncidentSeverity, name="incident_severity_enum", native_enum=False),
        nullable=False,
        default=IncidentSeverity.MEDIUM,
    )
    status: Mapped[IncidentStatus] = mapped_column(
        SAEnum(IncidentStatus, name="incident_status_enum", native_enum=False),
        nullable=False,
        default=IncidentStatus.DETECTED,
        index=True,
    )
    service_hint: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
    investigation_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    trigger_payload: Mapped[dict[str, Any]] = mapped_column(
        JSON_TYPE,
        nullable=False,
        default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    runs: Mapped[list["InvestigationRun"]] = relationship(
        "InvestigationRun",
        back_populates="incident",
        cascade="all, delete-orphan",
        order_by="InvestigationRun.created_at.desc()",
    )

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("status", IncidentStatus.DETECTED)
        kwargs.setdefault("environment", IncidentEnvironment.DEVELOPMENT)
        kwargs.setdefault("severity", IncidentSeverity.MEDIUM)
        kwargs.setdefault("trigger_payload", {})
        kwargs.setdefault("detected_at", utc_now())
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        status_val = self.status.value if self.status is not None else "UNSET"
        return f"<Incident id={self.id} title={self.title!r} status={status_val}>"


class InvestigationRun(Base):
    """Represents an execution attempt of an automated investigation for an incident."""

    __tablename__ = "investigation_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    incident_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[InvestigationRunStatus] = mapped_column(
        SAEnum(InvestigationRunStatus, name="investigation_run_status_enum", native_enum=False),
        nullable=False,
        default=InvestigationRunStatus.PENDING,
        index=True,
    )

    # Runtime configuration metadata (deferred to future passes; null for now)
    runtime_model_provider: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    runtime_model_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    prompt_context_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Configurations
    retrieval_config: Mapped[dict[str, Any]] = mapped_column(
        JSON_TYPE,
        nullable=False,
        default=dict,
    )
    budget_config: Mapped[dict[str, Any]] = mapped_column(
        JSON_TYPE,
        nullable=False,
        default=dict,
    )
    code_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Execution timestamps & outcome
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    stop_reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    root_cause_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    failure_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Audit timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    incident: Mapped["Incident"] = relationship(
        "Incident",
        back_populates="runs",
    )

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("status", InvestigationRunStatus.PENDING)
        kwargs.setdefault("retrieval_config", {})
        kwargs.setdefault("budget_config", {})
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        status_val = self.status.value if self.status is not None else "UNSET"
        return f"<InvestigationRun id={self.id} incident_id={self.incident_id} status={status_val}>"
