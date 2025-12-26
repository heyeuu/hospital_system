"""Data access layer built on SQLAlchemy sessions."""

from datetime import date, datetime
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import models
from .exceptions import ResourceNotFoundError


class DepartmentRepository:
    """CRUD operations for Department."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, name: str, description: str | None = None) -> models.Department:
        department = models.Department(name=name, description=description)
        self.session.add(department)
        self.session.flush()
        return department

    def get(self, department_id: int) -> models.Department:
        department = self.session.get(models.Department, department_id)
        if department is None:
            raise ResourceNotFoundError(f"Department {department_id} not found.")
        return department

    def get_by_name(self, name: str) -> models.Department:
        result = self.session.execute(select(models.Department).where(models.Department.name == name))
        department = result.scalar_one_or_none()
        if department is None:
            raise ResourceNotFoundError(f"Department '{name}' not found.")
        return department

    def list(self) -> Sequence[models.Department]:
        return self.session.scalars(select(models.Department)).all()


class DoctorRepository:
    """CRUD operations for Doctor."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        name: str,
        department_id: int,
        specialization: str | None = None,
        contact: str | None = None,
    ) -> models.Doctor:
        doctor = models.Doctor(
            name=name,
            department_id=department_id,
            specialization=specialization,
            contact=contact,
        )
        self.session.add(doctor)
        self.session.flush()
        return doctor

    def get(self, doctor_id: int) -> models.Doctor:
        doctor = self.session.get(models.Doctor, doctor_id)
        if doctor is None:
            raise ResourceNotFoundError(f"Doctor {doctor_id} not found.")
        return doctor

    def list(self) -> Sequence[models.Doctor]:
        return self.session.scalars(select(models.Doctor)).all()


class PatientRepository:
    """CRUD operations for Patient."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        name: str,
        date_of_birth=None,
        contact_info: str | None = None,
        address: str | None = None,
    ) -> models.Patient:
        patient = models.Patient(
            name=name, date_of_birth=date_of_birth, contact_info=contact_info, address=address
        )
        self.session.add(patient)
        self.session.flush()
        return patient

    def get(self, patient_id: int) -> models.Patient:
        patient = self.session.get(models.Patient, patient_id)
        if patient is None:
            raise ResourceNotFoundError(f"Patient {patient_id} not found.")
        return patient

    def list(self) -> Sequence[models.Patient]:
        return self.session.scalars(select(models.Patient)).all()


class RegistrationRepository:
    """CRUD operations for Registration."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        patient_id: int,
        doctor_id: int,
        department_id: int,
        visit_time,
        status: str = "scheduled",
        symptoms: str | None = None,
    ) -> models.Registration:
        registration = models.Registration(
            patient_id=patient_id,
            doctor_id=doctor_id,
            department_id=department_id,
            visit_time=visit_time,
            status=status,
            symptoms=symptoms,
        )
        self.session.add(registration)
        self.session.flush()
        return registration

    def get(self, registration_id: int) -> models.Registration:
        registration = self.session.get(models.Registration, registration_id)
        if registration is None:
            raise ResourceNotFoundError(f"Registration {registration_id} not found.")
        return registration

    def exists_conflict(self, doctor_id: int, visit_time: datetime) -> bool:
        """Check if a doctor already has a registration at the same minute and not cancelled."""
        time_key = visit_time.strftime("%Y-%m-%d %H:%M")
        stmt = select(func.count()).where(
            models.Registration.doctor_id == doctor_id,
            func.strftime("%Y-%m-%d %H:%M", models.Registration.visit_time) == time_key,
            models.Registration.status != "已取消",
        )
        return bool(self.session.execute(stmt).scalar_one())

    def exists_patient_conflict(self, patient_id: int, visit_time: datetime) -> bool:
        """Check if a patient already has a registration at the same minute and not cancelled."""
        time_key = visit_time.strftime("%Y-%m-%d %H:%M")
        stmt = select(func.count()).where(
            models.Registration.patient_id == patient_id,
            func.strftime("%Y-%m-%d %H:%M", models.Registration.visit_time) == time_key,
            models.Registration.status != "已取消",
        )
        return bool(self.session.execute(stmt).scalar_one())

    def list(
        self,
        department_id: int | None = None,
        visit_date: date | None = None,
        status: str | None = None,
        **_unused,
    ) -> Sequence[models.Registration]:
        stmt = select(models.Registration)
        if department_id is not None:
            stmt = stmt.where(models.Registration.department_id == department_id)
        if visit_date is not None:
            stmt = stmt.where(func.date(models.Registration.visit_time) == visit_date)
        if status:
            stmt = stmt.where(models.Registration.status == status)
        return self.session.scalars(stmt).all()

    def list_by_patient(self, patient_id: int) -> Sequence[models.Registration]:
        return self.session.scalars(
            select(models.Registration).where(models.Registration.patient_id == patient_id)
        ).all()
