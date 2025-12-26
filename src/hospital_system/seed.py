"""Initial data seeding for the hospital system."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from hospital_system import HospitalService, init_db, session_scope
from hospital_system.exceptions import ResourceNotFoundError


def seed() -> None:
    """Populate the database with starter departments, doctors, and patients."""
    init_db()
    with session_scope() as session:
        service = HospitalService(session)

        departments = [
            "内科",
            "外科",
            "妇科",
            "儿科",
            "骨科",
            "眼科",
            "口腔科",
        ]

        department_ids: dict[str, int] = {}
        for name in departments:
            try:
                department = service.departments.get_by_name(name)
            except ResourceNotFoundError:
                department = service.create_department(name=name)
                print(f"[dept] created {name}")
            else:
                print(f"[dept] exists {name}")
            department_ids[name] = department.id

        doctors_seed = [
            ("张伟", "内科"),
            ("李军", "内科"),
            ("王芳", "外科"),
            ("赵敏", "妇科"),
            ("陈涛", "儿科"),
            ("刘洋", "骨科"),
            ("周磊", "眼科"),
            ("孙莉", "口腔科"),
        ]

        for name, dept_name in doctors_seed:
            dept_id = department_ids[dept_name]
            # Avoid duplicates per name and department
            existing = [
                d for d in service.list_doctors() if d.name == name and d.department_id == dept_id
            ]
            if existing:
                print(f"[doctor] exists {name} - {dept_name}")
                continue
            service.create_doctor(name=name, department_id=dept_id)
            print(f"[doctor] created {name} - {dept_name}")

        patients_seed = [
            ("王强", date(1985, 5, 12)),
            ("李娜", date(1990, 8, 23)),
            ("陈刚", date(1978, 3, 5)),
            ("赵雪", date(2001, 11, 30)),
            ("周晨", date(2010, 4, 15)),
            ("刘梅", date(1968, 9, 2)),
        ]

        existing_patients = {p.name for p in service.list_patients()}
        for name, dob in patients_seed:
            if name in existing_patients:
                print(f"[patient] exists {name}")
                continue
            service.create_patient(name=name, date_of_birth=dob)
            print(f"[patient] created {name}")

        # Optionally seed a handful of registrations for demo purposes
        doctors = service.list_doctors()
        patients = service.list_patients()
        if doctors and patients:
            now = datetime.now()
            for idx, patient in enumerate(patients[:3]):
                doctor = doctors[idx % len(doctors)]
                department_id = doctor.department_id
                visit_time = now + timedelta(days=idx + 1, hours=9)
                service.create_registration(
                    patient_id=patient.id,
                    doctor_id=doctor.id,
                    department_id=department_id,
                    visit_time=visit_time,
                    symptoms="示例症状",
                )
            print("[registration] seeded sample registrations")


if __name__ == "__main__":
    seed()
