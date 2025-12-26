"""Business logic layer for the hospital system."""

from datetime import date, datetime
from typing import Sequence

from sqlalchemy.orm import Session

from .exceptions import ValidationError
from .models import Department, Doctor, Patient, Registration
from .repositories import (
    DepartmentRepository,
    DoctorRepository,
    PatientRepository,
    RegistrationRepository,
)


class HospitalService:
    """Facade that encapsulates use cases and business rules."""

    def __init__(self, session: Session):
        self.departments = DepartmentRepository(session)
        self.doctors = DoctorRepository(session)
        self.patients = PatientRepository(session)
        self.registrations = RegistrationRepository(session)

    # Department
    def create_department(self, name: str, description: str | None = None) -> Department:
        return self.departments.create(name=name, description=description)

    def list_departments(self) -> Sequence[Department]:
        return self.departments.list()

    # Doctor
    def create_doctor(
        self, name: str, department_id: int, specialization: str | None = None, contact: str | None = None
    ) -> Doctor:
        # Ensure department exists
        self.departments.get(department_id)
        return self.doctors.create(
            name=name, department_id=department_id, specialization=specialization, contact=contact
        )

    def list_doctors(self) -> Sequence[Doctor]:
        return self.doctors.list()

    # Patient
    def create_patient(
        self,
        name: str,
        date_of_birth=None,
        contact_info: str | None = None,
        address: str | None = None,
    ) -> Patient:
        if not name.strip():
            raise ValidationError("Patient name cannot be empty.")
        return self.patients.create(
            name=name, date_of_birth=date_of_birth, contact_info=contact_info, address=address
        )

    def list_patients(self) -> Sequence[Patient]:
        return self.patients.list()

    # Registration
    def create_registration(
        self,
        patient_id: int,
        doctor_id: int,
        department_id: int,
        visit_time: datetime,
        status: str = "scheduled",
        symptoms: str | None = None,
    ) -> Registration:
        patient = self.patients.get(patient_id)
        doctor = self.doctors.get(doctor_id)
        department = self.departments.get(department_id)

        if doctor.department_id != department.id:
            raise ValidationError("Doctor must belong to the selected department.")
        if visit_time < datetime.now():
            raise ValidationError("Visit time cannot be in the past.")

        return self.registrations.create(
            patient_id=patient.id,
            doctor_id=doctor.id,
            department_id=department.id,
            visit_time=visit_time,
            status=status,
            symptoms=symptoms,
        )

    def list_registrations(self, *args, **kwargs) -> Sequence[Registration]:
        """List registrations with optional filters; tolerant to positional/keyword usage."""
        department_id = kwargs.pop("department_id", None)
        visit_date = kwargs.pop("visit_date", None)
        status = kwargs.pop("status", None)

        # Fallback to positional overrides for backward compatibility
        if args:
            if len(args) >= 1 and department_id is None:
                department_id = args[0]
            if len(args) >= 2 and visit_date is None:
                visit_date = args[1]

        return self.registrations.list(
            department_id=department_id, visit_date=visit_date, status=status
        )

    def get_registration(self, registration_id: int) -> Registration:
        return self.registrations.get(registration_id)

    def complete_registration(self, registration_id: int) -> Registration:
        """Mark a registration as completed."""
        registration = self.registrations.get(registration_id)
        registration.status = "completed"
        # Ensure persistence immediately for UI refresh scenarios.
        self.registrations.session.flush()
        self.registrations.session.commit()
        return registration

    def delete_registration(self, registration_id: int) -> None:
        """Delete a registration record."""
        registration = self.registrations.get(registration_id)
        self.registrations.session.delete(registration)
        self.registrations.session.commit()
