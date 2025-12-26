"""医院门诊挂号系统包。"""

from .db import Base, engine, session_scope
from .exceptions import (
    DatabaseConnectionError,
    ResourceNotFoundError,
    TimeSlotOccupiedError,
    ValidationError,
    DoctorBusyError,
    PatientBusyError,
)
from .models import Department, Doctor, Patient, Registration
from .services import HospitalService

__all__ = [
    "Base",
    "engine",
    "session_scope",
    "HospitalService",
    "Department",
    "Doctor",
    "Patient",
    "Registration",
    "DatabaseConnectionError",
    "ResourceNotFoundError",
    "ValidationError",
    "TimeSlotOccupiedError",
    "DoctorBusyError",
    "PatientBusyError",
]


def init_db() -> None:
    """Create database tables."""
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as exc:  # noqa: BLE001
        raise DatabaseConnectionError("Failed to initialize database schema.") from exc
