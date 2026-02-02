import frappe
from frappe.utils import getdate, get_datetime

def process_auto_attendance():
    today = getdate()

    employees = frappe.get_all(
        "Employee",
        filters={"status": "Active"},
        fields=["name", "shift_type"]
    )

    for emp in employees:
        if not emp.shift_type:
            continue

        shift = frappe.get_doc("shift type", emp.shift_type)

        shift_start = get_datetime(f"{today} {shift.shift_start_time}")
        shift_end = get_datetime(f"{today} {shift.shift_end_time}")

        checkins = frappe.get_all(
            "Employee Checkin",
            filters={
                "employee": emp.name,
                "time": ["between", [shift_start, shift_end]]
            },
            fields=["log_type", "time"],
            order_by="time asc"
        )

        # ❌ no logs
        if not checkins:
            create_attendance(emp.name, today, "Absent")
            continue

        last_log = checkins[-1]

        # ✅ ONLY if last log is OUT
        if last_log.log_type == "OUT":
            create_attendance(emp.name, today, "Present")
        else:
            create_attendance(emp.name, today, "Absent")


def create_attendance(employee, date, status):
    if frappe.db.exists("Attendence", {
        "employee": employee,
        "attendence_date": date
    }):
        return

    att = frappe.new_doc("Attendence")
    att.employee = employee
    att.attendence_date = date
    att.status = status
    att.insert(ignore_permissions=True)
    att.submit()
