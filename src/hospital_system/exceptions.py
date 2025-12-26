"""Custom exceptions used across the hospital system package."""


class DatabaseConnectionError(Exception):
    """Raised when the database connection cannot be established."""


class ResourceNotFoundError(Exception):
    """Raised when an entity lookup returns no result."""


class ValidationError(Exception):
    """Raised when incoming data fails domain or business validation."""


class TimeSlotOccupiedError(Exception):
    """Raised when a doctor already has an appointment at the requested time."""


class DoctorBusyError(Exception):
    """Raised when a doctor is busy within the protected interval."""


class PatientBusyError(Exception):
    """Raised when a patient already has an appointment in the protected interval."""


__all__ = [
    "DatabaseConnectionError",
    "ResourceNotFoundError",
    "ValidationError",
    "TimeSlotOccupiedError",
    "DoctorBusyError",
    "PatientBusyError",
]
