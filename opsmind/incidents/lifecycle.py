"""Incident and investigation run lifecycle policies and guardrails."""

from opsmind.incidents.models import IncidentStatus, InvestigationRunStatus

# Statuses of an incident where starting an automated investigation is allowed
INVESTIGATABLE_INCIDENT_STATUSES: frozenset[IncidentStatus] = frozenset(
    {
        IncidentStatus.DETECTED,
        IncidentStatus.TRIAGING,
        IncidentStatus.INVESTIGATING,
        IncidentStatus.INCONCLUSIVE,
        IncidentStatus.INVESTIGATION_FAILED,
    }
)

# Statuses of an incident where starting a new investigation must be rejected
NON_INVESTIGATABLE_INCIDENT_STATUSES: frozenset[IncidentStatus] = frozenset(
    {
        IncidentStatus.ROOT_CAUSE_PROPOSED,
        IncidentStatus.REMEDIATION_PROPOSED,
        IncidentStatus.RESOLVED,
        IncidentStatus.POSTMORTEM_COMPLETE,
        IncidentStatus.CANCELLED,
    }
)

# Investigation run statuses considered active (concurrency guardrail)
ACTIVE_INVESTIGATION_STATUSES: frozenset[InvestigationRunStatus] = frozenset(
    {
        InvestigationRunStatus.PENDING,
        InvestigationRunStatus.RUNNING,
    }
)


def is_incident_investigatable(status: IncidentStatus) -> bool:
    """Check if an incident in the given status is eligible for investigation."""
    return status in INVESTIGATABLE_INCIDENT_STATUSES


def is_run_active(status: InvestigationRunStatus) -> bool:
    """Check if an investigation run is currently active (PENDING or RUNNING)."""
    return status in ACTIVE_INVESTIGATION_STATUSES
