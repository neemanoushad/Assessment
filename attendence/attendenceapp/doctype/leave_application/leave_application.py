import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate


class LeaveApplication(Document):

    def validate(self):
        if self.from_date > self.to_date:
            frappe.throw("Invalid date range. The To Date must be greater than or equal to the From Date.")
        return

    def before_submit(self):
        if self.status not in ("Approved", "Rejected"):
            frappe.throw("Only Leave Applications with status 'Approved' or 'Rejected' can be submitted")

        balance = get_leave_balance(self.employee)
        row = balance.get(self.leave_type)

        if not row:
            frappe.throw(f"No Leave Allocation found for Leave Type {self.leave_type}")

        if self.total_leave_days > row.get("remaining_leaves", 0):
            frappe.throw(
                f"Insufficient leave balance for Leave Type {self.leave_type}"
            )


@frappe.whitelist()
def get_leave_balance(employee):
    allocations = frappe.get_all(
        "Leaves Allocation",
        filters={"employee": employee, "docstatus": 1},
        fields=["leave_type", "new_leave_allocated", "to_date"]
    )

    data = {}
    today = getdate()

    # Build allocation data
    for a in allocations:
        lt = a.get("leave_type")
        alloc = flt(a.get("new_leave_allocated") or 0)

        expired = 0
        to_date = a.get("to_date")
        if to_date and getdate(to_date) < today:
            expired = alloc

        data[lt] = {
            "total_leaves": alloc,
            "expired_leaves": expired,
            "leaves_taken": 0,
            "leaves_pending_approval": 0,
            "remaining_leaves": alloc - expired,
        }

    # ✅ Fetch ALL non-rejected leave applications (approved + pending)
    leaves = frappe.get_all(
        "Leave Application",
        filters={
            "employee": employee,
            "docstatus": ["<", 2],        # draft + submitted
            "status": ["!=", "Rejected"]  # ignore rejected
        },
        fields=["leave_type", "total_leave_days", "status"]
    )

    # Process leaves
    for l in leaves:
        lt = l.get("leave_type")
        days = flt(l.get("total_leave_days") or 0)
        status = l.get("status")

        if lt not in data:
            data[lt] = {
                "total_leaves": 0,
                "expired_leaves": 0,
                "leaves_taken": 0,
                "leaves_pending_approval": 0,
                "remaining_leaves": 0,
            }

        if status == "Approved":
            data[lt]["leaves_taken"] += days
        else:  # Open / Pending Approval
            data[lt]["leaves_pending_approval"] += days

    # Final remaining calculation
    for lt in data:
        total = data[lt]["total_leaves"]
        used = data[lt]["leaves_taken"]
        pending = data[lt]["leaves_pending_approval"]
        expired = data[lt]["expired_leaves"]

        data[lt]["remaining_leaves"] = total - used - pending - expired

    return data
