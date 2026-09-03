"""Common domain error definitions."""

from typing import Any


class OpsMindError(Exception):
    """Base exception for all OpsMind domain errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class DatabaseError(OpsMindError):
    """Raised when a database operation fails."""


class EntityNotFoundError(OpsMindError):
    """Raised when a requested domain entity cannot be found."""


class ValidationError(OpsMindError):
    """Raised when entity data fails domain validation."""
