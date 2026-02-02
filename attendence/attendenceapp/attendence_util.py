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
        # skip if no shift assigned
        if not emp.shift_type:
            continue

        # get shift doc (your custom Shift Type)
        shift = frappe.get_doc("shift type", emp.shift_type)

        shift_start = get_datetime(f"{today} {shift.shift_start_time}")
        shift_end = get_datetime(f"{today} {shift.shift_end_time}")

        # check checkins within shift time
        checkins = frappe.get_all(
            "Employee Checkin",
            filters={
                "employee": emp.name,
                "time": ["between", [shift_start, shift_end]]
            },
            fields=["employee", "time"]
        )

        if not checkins:
            create_attendance(emp.name, today, "Absent")
        else:
            create_attendance(emp.name, today, "Present")


def create_attendance(employee, date, status):
    # ✅ prevent duplicate attendance
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
