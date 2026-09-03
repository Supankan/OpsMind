"""Common UUID utilities."""

import uuid


def generate_uuid() -> uuid.UUID:
    """Generate a random UUIDv4."""
    return uuid.uuid4()


def is_valid_uuid(val: str) -> bool:
    """Validate whether a string is a valid UUID."""
    try:
        uuid.UUID(str(val))
        return True
    except (ValueError, AttributeError, TypeError):
        return False
