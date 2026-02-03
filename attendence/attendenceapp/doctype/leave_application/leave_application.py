import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate, add_days


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

    def on_submit(self):
        if self.status == "Approved":
            self.create_leave_attendance()
            self.reduce_leave_balance()

    def reduce_leave_balance(self):
        """
        Do NOT reduce Leaves Allocation.new_leave_allocated.
        It should always represent TOTAL allocated leaves.
        Balance is handled only in get_leave_balance().
        """
        return

    def create_leave_attendance(self):
        current_date = self.from_date

        while current_date <= self.to_date:
            existing = frappe.db.exists(
                "Attendence",
                {"employee": self.employee, "attendence_date": current_date}
            )

            if not existing:
                att = frappe.new_doc("Attendence")
                att.employee = self.employee
                att.attendence_date = current_date
                att.status = "On Leave"
                att.leave_type = self.leave_type
                att.insert(ignore_permissions=True)
                att.submit()

            current_date = add_days(current_date, 1)


@frappe.whitelist()
def get_leave_balance(employee):
    allocations = frappe.get_all(
        "Leaves Allocation",
        filters={"employee": employee, "docstatus": 1},
        fields=["leave_type", "new_leave_allocated", "to_date"]
    )

    data = {}
    today = getdate()

    # allocations (total quota)
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

    # include Draft + Submitted, exclude Rejected
    leaves = frappe.get_all(
        "Leave Application",
        filters={
            "employee": employee,
            "docstatus": ["<", 2],
            "status": ["!=", "Rejected"]
        },
        fields=["leave_type", "total_leave_days", "status", "docstatus"]
    )

    for l in leaves:
        lt = l.get("leave_type")
        days = flt(l.get("total_leave_days") or 0)
        status = l.get("status")
        docstatus = l.get("docstatus")

        if lt not in data:
            data[lt] = {
                "total_leaves": 0,
                "expired_leaves": 0,
                "leaves_taken": 0,
                "leaves_pending_approval": 0,
                "remaining_leaves": 0,
            }

        # ONLY count as taken when Approved + Submitted
        if status == "Approved" and docstatus == 1:
            data[lt]["leaves_taken"] += days

        #  ONLY count as pending when NOT Approved (Draft or Submitted)
        elif status != "Approved":
            data[lt]["leaves_pending_approval"] += days

        #  Approved + Draft → do nothing (neither taken nor pending)

    # final remaining calculation
    for lt in data:
        total = data[lt]["total_leaves"]
        expired = data[lt]["expired_leaves"]
        used = data[lt]["leaves_taken"]

        data[lt]["remaining_leaves"] = max(0, total - used - expired)

    return data
