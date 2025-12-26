"""SQLAlchemy ORM models for the hospital system."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    doctors: Mapped[list["Doctor"]] = relationship("Doctor", back_populates="department")
    registrations: Mapped[list["Registration"]] = relationship(
        "Registration", back_populates="department"
    )

    def __repr__(self) -> str:
        return f"<Department id={self.id} name={self.name}>"


class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    specialization: Mapped[str | None] = mapped_column(String(100), nullable=True)
    contact: Mapped[str | None] = mapped_column(String(120), nullable=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), nullable=False)

    department: Mapped[Department] = relationship("Department", back_populates="doctors")
    registrations: Mapped[list["Registration"]] = relationship(
        "Registration", back_populates="doctor"
    )

    def __repr__(self) -> str:
        return f"<Doctor id={self.id} name={self.name}>"


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    contact_info: Mapped[str | None] = mapped_column(String(120), nullable=True)
    address: Mapped[str | None] = mapped_column(String(200), nullable=True)

    registrations: Mapped[list["Registration"]] = relationship(
        "Registration", back_populates="patient"
    )

    def __repr__(self) -> str:
        return f"<Patient id={self.id} name={self.name}>"


class Registration(Base):
    __tablename__ = "registrations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), nullable=False)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), nullable=False)
    visit_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="scheduled")
    symptoms: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    patient: Mapped[Patient] = relationship("Patient", back_populates="registrations")
    doctor: Mapped[Doctor] = relationship("Doctor", back_populates="registrations")
    department: Mapped[Department] = relationship("Department", back_populates="registrations")

    def __repr__(self) -> str:
        return (
            f"<Registration id={self.id} patient_id={self.patient_id} "
            f"doctor_id={self.doctor_id} status={self.status}>"
        )
