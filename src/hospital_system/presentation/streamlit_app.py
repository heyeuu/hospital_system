"""Streamlit presentation layer that consumes the business services."""

from datetime import date, datetime, time

import pandas as pd
import plotly.express as px
import streamlit as st

from hospital_system.db import Base, engine, session_scope

try:
    from hospital_system.exceptions import (
        DatabaseConnectionError,
        ResourceNotFoundError,
        TimeSlotOccupiedError,
        ValidationError,
        DoctorBusyError,
        PatientBusyError,
    )
except ImportError:
    # Fallback for environments where the new exception is not yet available
    from hospital_system.exceptions import (  # type: ignore
        DatabaseConnectionError,
        ResourceNotFoundError,
        ValidationError,
    )

    class TimeSlotOccupiedError(Exception):  # type: ignore
        """Fallback placeholder if import fails."""

    class DoctorBusyError(Exception):  # type: ignore
        """Fallback placeholder if import fails."""

    class PatientBusyError(Exception):  # type: ignore
        """Fallback placeholder if import fails."""

from hospital_system.services import HospitalService


Base.metadata.create_all(bind=engine)


def render_dashboard(service: HospitalService) -> None:
    st.subheader("全院概览 (Dashboard)")

    registrations = get_registrations(service)
    total_reg = len(registrations)

    visited_statuses = {"completed", "done", "finished", "已就诊", "已完成"}
    visited_statuses_lower = {s.lower() for s in visited_statuses}
    visited = sum(
        1
        for reg in registrations
        if (reg.status or "").lower() in visited_statuses_lower or reg.status in visited_statuses
    )
    waiting = total_reg - visited

    col1, col2, col3 = st.columns(3)
    col1.metric("总挂号单数", total_reg)
    col2.metric("已就诊人数", visited)
    col3.metric("待就诊人数", waiting)

    if registrations:
        df = pd.DataFrame(
            [{"department": reg.department.name, "status": reg.status} for reg in registrations]
        )
        dept_counts = df.groupby("department").size().reset_index(name="挂号数")
        dept_counts = dept_counts.sort_values("挂号数", ascending=False)
        left_space, chart_bridge, right_space = st.columns([1, 2, 1])
        with chart_bridge:
            fig = px.bar(
                dept_counts,
                x="department",
                y="挂号数",
                text="挂号数",
                color_discrete_sequence=["#2a7de1"],  # medical blue
            )
            fig.update_traces(
                width=0.35,
                hovertemplate="%{x}<br>挂号数: %{y}<extra></extra>",
                textposition="outside",
                marker_line_color="#1f4f8f",
                marker_line_width=0.6,
            )
            fig.update_layout(
                xaxis_title="科室",
                yaxis_title="挂号数",
                xaxis=dict(tickangle=0, showgrid=False, tickfont=dict(color="#0f1a2b", size=12)),
                yaxis=dict(
                    showgrid=False,
                    tickfont=dict(color="#0f1a2b", size=12),
                    tick0=0,
                    dtick=1,
                    rangemode="tozero",
                ),
                plot_bgcolor="white",
                paper_bgcolor="white",
                font=dict(color="#0f1a2b", size=14),
                margin=dict(t=40, b=40, l=10, r=10),
                bargap=0.5,
                width=720,  # fixed figure width to avoid overly wide bars when few departments
            )
            st.plotly_chart(fig, use_container_width=False, height=350)
    else:
        st.info("暂无挂号数据。")


def get_registrations(
    service: HospitalService, department_id=None, visit_date=None, status=None
):
    """Fetch registrations with graceful fallback for different service signatures."""
    regs = []
    try:
        regs = service.list_registrations(
            department_id=department_id, visit_date=visit_date, status=status
        )
    except TypeError:
        # Fallback for older Service signature; call repository directly
        try:
            regs = service.registrations.list(
                department_id=department_id, visit_date=visit_date, status=status
            )
        except TypeError:
            regs = service.registrations.list()

    # Final in-memory filtering to guarantee UI honors filters even if service signature differs.
    filtered = []
    for reg in regs:
        if department_id is not None and reg.department_id != department_id:
            continue
        if visit_date is not None and reg.visit_time.date() != visit_date:
            continue
        normalized_status = (reg.status or "").strip()
        if normalized_status == "":
            normalized_status = None
        if status is not None:
            if status == "__NONE__" and normalized_status is not None:
                continue
            if status != "__NONE__" and normalized_status != status:
                continue
        filtered.append(reg)
    return filtered


def complete_registration_safe(service: HospitalService, registration_id: int) -> None:
    """Complete a registration even if the service interface changes."""
    try:
        service.complete_registration(registration_id)
        return
    except AttributeError:
        # Fall back to direct repository update
        try:
            reg = service.registrations.get(registration_id)
            reg.status = "completed"
            try:
                service.registrations.session.commit()
            except Exception:
                service.registrations.session.rollback()
                raise
        except Exception as exc:  # noqa: BLE001
            raise exc
    except ValidationError as exc:
        raise exc


def delete_registration_safe(service: HospitalService, registration_id: int) -> None:
    """Delete a registration even if the service interface changes."""
    try:
        service.delete_registration(registration_id)
        return
    except AttributeError:
        try:
            reg = service.registrations.get(registration_id)
            service.registrations.session.delete(reg)
            try:
                service.registrations.session.commit()
            except Exception:
                service.registrations.session.rollback()
                raise
        except Exception as exc:  # noqa: BLE001
            raise exc
    except ValidationError as exc:
        raise exc


def render_create_entities(service: HospitalService) -> None:
    st.subheader("基础资料管理")
    with st.expander("新增科室"):
        with st.form("create_department"):
            name = st.text_input("科室名称")
            description = st.text_area("科室描述", height=80)
            submitted = st.form_submit_button("创建科室")
            if submitted and name:
                try:
                    service.create_department(name=name, description=description or None)
                    st.success("科室已创建")
                except Exception as exc:  # noqa: BLE001 - presentation layer catch-all
                    st.error(f"创建失败: {exc}")

    with st.expander("新增医生"):
        departments = service.list_departments()
        if not departments:
            st.info("请先创建科室，再添加医生。")
        else:
            with st.form("create_doctor"):
                name = st.text_input("医生姓名", key="doctor_name")
                specialization = st.text_input("擅长/职称", key="doctor_specialization")
                contact = st.text_input("联系方式", key="doctor_contact")
                department_options = {f"{dept.name} (#{dept.id})": dept.id for dept in departments}
                department_display = st.selectbox("所属科室", list(department_options.keys()))
                submitted = st.form_submit_button("创建医生")
                if submitted:
                    try:
                        department_id = department_options.get(department_display)
                        service.create_doctor(
                            name=name,
                            department_id=department_id,
                            specialization=specialization or None,
                            contact=contact or None,
                        )
                        st.success("医生已创建")
                    except Exception as exc:  # noqa: BLE001
                        st.error(f"创建失败: {exc}")

    with st.expander("新增患者"):
        with st.form("create_patient"):
            name = st.text_input("患者姓名", key="patient_name")
            record_birth = st.checkbox("填写出生日期", key="patient_birth_toggle")
            birth_date = None
            if record_birth:
                birth_date = st.date_input("出生日期", key="patient_birth")
            contact = st.text_input("联系方式", key="patient_contact")
            address = st.text_area("联系地址", key="patient_address", height=60)
            submitted = st.form_submit_button("创建患者")
            if submitted:
                try:
                    service.create_patient(
                        name=name,
                        date_of_birth=birth_date,
                        contact_info=contact or None,
                        address=address or None,
                    )
                    st.success("患者已创建")
                except ValidationError as exc:
                    st.warning(str(exc))
                except Exception as exc:  # noqa: BLE001
                    st.error(f"创建失败: {exc}")


def render_registration(service: HospitalService) -> None:
    st.subheader("门诊挂号")

    patients = service.list_patients()
    doctors = service.list_doctors()
    departments = service.list_departments()
    all_registrations = get_registrations(service)

    if not patients or not doctors or not departments:
        st.info("请先完成患者、医生、科室的基础信息录入。")
        return

    patient_options = {f"{p.name} (#{p.id})": p.id for p in patients}
    doctor_options = {f"{d.name} - {d.department.name} (#{d.id})": d.id for d in doctors}
    department_options = {f"{dept.name} (#{dept.id})": dept.id for dept in departments}

    with st.form("create_registration"):
        patient_display = st.selectbox("患者", list(patient_options.keys()))
        department_display = st.selectbox("就诊科室", list(department_options.keys()))
        doctor_display = st.selectbox("接诊医生", list(doctor_options.keys()))
        visit_date = st.date_input("就诊日期")
        visit_time = st.time_input("就诊时间", value=time(9, 0))
        symptoms = st.text_area("主诉/症状", height=80)
        submitted = st.form_submit_button("确认挂号")

        if submitted:
            try:
                visit_at = datetime.combine(visit_date, visit_time)
                registration = service.create_registration(
                    patient_id=patient_options[patient_display],
                    doctor_id=doctor_options[doctor_display],
                    department_id=department_options[department_display],
                    visit_time=visit_at,
                    symptoms=symptoms or None,
                )
                st.success(f"挂号成功，单号 #{registration.id}")
            except (ValidationError, ResourceNotFoundError) as exc:
                st.warning(str(exc))
            except (TimeSlotOccupiedError, DoctorBusyError):
                st.error("抱歉，该医生的该时段已被占用，请刷新后选择其他时段")
            except PatientBusyError:
                st.error("抱歉，该患者在该时段已有预约，请刷新后选择其他时段")
            except Exception as exc:  # noqa: BLE001
                st.error(f"挂号失败: {exc}")

    st.markdown("#### 当前挂号列表")
    dept_filter_options = {"全部": None}
    dept_filter_options.update({dept.name: dept.id for dept in departments})

    filter_col1, filter_col2, filter_col3 = st.columns([1, 1, 1])
    with filter_col1:
        selected_dept_key = st.selectbox("按科室筛选", list(dept_filter_options.keys()))
        selected_dept_id = dept_filter_options[selected_dept_key]
    with filter_col2:
        date_values = sorted({reg.visit_time.date() for reg in all_registrations})
        date_options = {"全部": None}
        date_options.update({str(d): d for d in date_values})
        selected_date_label = st.selectbox("按就诊日期筛选", list(date_options.keys()))
        selected_visit_date = date_options[selected_date_label]
    with filter_col3:
        status_values = { (reg.status or "未指定").strip() or "未指定" for reg in all_registrations }
        status_options = {"全部": None}
        status_options.update({label: ("__NONE__" if label == "未指定" else label) for label in sorted(status_values)})
        selected_status_key = st.selectbox("按状态筛选", list(status_options.keys()))
        selected_status_value = status_options[selected_status_key]

    filtered_registrations = get_registrations(
        service,
        department_id=selected_dept_id,
        visit_date=selected_visit_date,
        status=selected_status_value,
    )

    for registration in filtered_registrations:
        col_info, col_action_complete, col_action_delete = st.columns([5, 1, 1])
        col_info.write(
            f"#{registration.id} | 患者: {registration.patient.name} | "
            f"医生: {registration.doctor.name} | 科室: {registration.department.name} | "
            f"时间: {registration.visit_time} | 状态: {registration.status}"
        )
        if (registration.status or "").lower() == "scheduled":
            if col_action_complete.button("确认就诊", key=f"complete_{registration.id}"):
                try:
                    complete_registration_safe(service, registration.id)
                    st.rerun()
                except ValidationError as exc:
                    col_action_complete.error(str(exc))
                except Exception as exc:  # noqa: BLE001
                    col_action_complete.error(f"更新失败: {exc}")

        if col_action_delete.button("删除记录", key=f"delete_{registration.id}"):
            try:
                delete_registration_safe(service, registration.id)
                st.rerun()
            except ValidationError as exc:
                col_action_delete.error(str(exc))
            except Exception as exc:  # noqa: BLE001
                col_action_delete.error(f"删除失败: {exc}")


def main() -> None:
    st.set_page_config(page_title="医院门诊挂号系统", page_icon="🏥", layout="wide")
    st.title("医院门诊挂号系统")

    try:
        with session_scope() as session:
            service = HospitalService(session)
            render_dashboard(service)
            st.divider()
            render_create_entities(service)
            st.divider()
            render_registration(service)
    except DatabaseConnectionError as exc:
        st.error(f"数据库连接失败: {exc}")


if __name__ == "__main__":
    main()
