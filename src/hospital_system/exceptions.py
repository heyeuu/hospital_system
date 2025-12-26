"""Custom exceptions used across the hospital system package."""


class DatabaseConnectionError(Exception):
    """Raised when the database connection cannot be established."""


class ResourceNotFoundError(Exception):
    """Raised when an entity lookup returns no result."""


class ValidationError(Exception):
    """Raised when incoming data fails domain or business validation."""
