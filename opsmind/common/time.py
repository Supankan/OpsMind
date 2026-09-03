"""Common datetime utilities."""

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Return current UTC datetime with timezone awareness."""
    return datetime.now(UTC)
