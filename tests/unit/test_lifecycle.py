"""Unit tests for incident and investigation run lifecycle policies."""

import pytest

from opsmind.incidents.lifecycle import (
    INVESTIGATABLE_INCIDENT_STATUSES,
    NON_INVESTIGATABLE_INCIDENT_STATUSES,
    is_incident_investigatable,
    is_run_active,
)
from opsmind.incidents.models import IncidentStatus, InvestigationRunStatus


@pytest.mark.parametrize(
    "status,expected",
    [
        (IncidentStatus.DETECTED, True),
        (IncidentStatus.TRIAGING, True),
        (IncidentStatus.INVESTIGATING, True),
        (IncidentStatus.INCONCLUSIVE, True),
        (IncidentStatus.INVESTIGATION_FAILED, True),
        (IncidentStatus.ROOT_CAUSE_PROPOSED, False),
        (IncidentStatus.REMEDIATION_PROPOSED, False),
        (IncidentStatus.RESOLVED, False),
        (IncidentStatus.POSTMORTEM_COMPLETE, False),
        (IncidentStatus.CANCELLED, False),
    ],
)
def test_is_incident_investigatable(status: IncidentStatus, expected: bool) -> None:
    """Verify that only the 5 approved statuses are eligible for investigation."""
    assert is_incident_investigatable(status) is expected


def test_lifecycle_status_partition_completeness() -> None:
    """Verify that all IncidentStatus values are accounted for with no overlap."""
    all_statuses = set(IncidentStatus)
    assert INVESTIGATABLE_INCIDENT_STATUSES.isdisjoint(NON_INVESTIGATABLE_INCIDENT_STATUSES)
    assert INVESTIGATABLE_INCIDENT_STATUSES | NON_INVESTIGATABLE_INCIDENT_STATUSES == all_statuses


@pytest.mark.parametrize(
    "status,expected",
    [
        (InvestigationRunStatus.PENDING, True),
        (InvestigationRunStatus.RUNNING, True),
        (InvestigationRunStatus.COMPLETED, False),
        (InvestigationRunStatus.FAILED, False),
        (InvestigationRunStatus.INCONCLUSIVE, False),
        (InvestigationRunStatus.CANCELLED, False),
    ],
)
def test_is_run_active(status: InvestigationRunStatus, expected: bool) -> None:
    """Verify that only PENDING and RUNNING runs are considered active."""
    assert is_run_active(status) is expected
