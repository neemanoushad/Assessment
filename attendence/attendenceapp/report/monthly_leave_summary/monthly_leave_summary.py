# Copyright (c) 2026, neema and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    columns, data = get_columns(), get_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": _("Employee ID"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 120},
        {"label": _("Employee Name"), "fieldname": "full_name", "fieldtype": "Data", "width": 200},
        {"label": _("Leave Type"), "fieldname": "leave_type", "fieldtype": "Data", "width": 140},
        {"label": _("Total Leaves Taken"), "fieldname": "leaves_taken", "fieldtype": "Float", "width": 140},
        {"label": _("Remaining Balance"), "fieldname": "remaining_balance", "fieldtype": "Float", "width": 140}
    ]


def get_data(filters):
    filters = filters or {}
    month = filters.get("month")
    year = filters.get("year")
    leave_type = filters.get("leave_type")
    
    # Return empty data if leave_type is not selected
    if not leave_type:
        return []
    
    # Convert to integers if provided
    if month:
        month = int(month)
    if year:
        year = int(year)

    data = []

    # Build conditions for Leave Application query
    leave_conditions = """
        status = 'Approved'
        AND docstatus = 1
    """
    leave_values = []

    if leave_type:
        leave_conditions += " AND leave_type = %s"
        leave_values.append(leave_type)

    if month and year:
        import datetime
        from datetime import date, timedelta
        first_day = date(year, month, 1)
        if month == 12:
            last_day = date(year + 1, 1, 1)
        else:
            last_day = date(year, month + 1, 1)
        last_day = last_day - timedelta(days=1)
        
        leave_conditions += " AND from_date >= %s AND to_date <= %s"
        leave_values.extend([first_day, last_day])

    # Get employees who have leave applications matching the filters
    leaves_query = f"""
        SELECT DISTINCT employee
        FROM `tabLeave Application`
        WHERE {leave_conditions}
    """
    
    employees_with_leaves = frappe.db.sql(leaves_query, tuple(leave_values), as_list=True)
    employee_names = [emp[0] for emp in employees_with_leaves]

    if not employee_names:
        return data

    for emp_name in employee_names:
        emp_record = frappe.get_doc("Employee", emp_name)
        
        # Get leaves taken
        leaves_conditions = f"""
            employee = %s
            AND status = 'Approved'
            AND docstatus = 1
        """
        leaves_values = [emp_name]

        if leave_type:
            leaves_conditions += " AND leave_type = %s"
            leaves_values.append(leave_type)

        if month and year:
            leaves_conditions += " AND from_date >= %s AND to_date <= %s"
            leaves_values.extend([first_day, last_day])

        leaves = frappe.db.sql(f"""
            SELECT SUM(total_leave_days) as total_days
            FROM `tabLeave Application`
            WHERE {leaves_conditions}
        """, tuple(leaves_values), as_dict=True)

        leaves_taken = leaves[0].get("total_days") or 0 if leaves else 0

        # Get leave allocation for this employee and leave type
        allocation = 0
        if leave_type:
            allocation_filters = {"employee": emp_name, "docstatus": 1, "leave_type": leave_type}
            allocation_record = frappe.get_value(
                "Leaves Allocation",
                allocation_filters,
                "new_leave_allocated"
            )
            allocation = allocation_record or 0

        data.append({
            "employee": emp_name,
            "full_name": emp_record.full_name,
            "leave_type": leave_type ,
            "leaves_taken": leaves_taken,
            "remaining_balance": allocation - leaves_taken
        })

    return data
