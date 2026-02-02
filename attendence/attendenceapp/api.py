import frappe

@frappe.whitelist(allow_guest=True)
def login_user(username, password):
    try:
        frappe.local.login_manager.authenticate(username, password)
        frappe.local.login_manager.post_login()

        return {
            "message": "Login successful",
            "user": frappe.session.user,
            "sid": frappe.session.sid
        }

    except frappe.AuthenticationError:
        frappe.throw("Invalid username or password")

@frappe.whitelist()
def receive_biometric_data(emp_code, punch_time, punch_type):
    log = frappe.new_doc("Biometric")
    log.employee_code = emp_code
    log.punch_time = punch_time
    log.punch_type = punch_type
    log.raw_data = frappe.as_json({
        "emp_code": emp_code,
        "punch_time": punch_time,
        "punch_type": punch_type
    })
    log.insert(ignore_permissions=True)

    return {"message": "Biometric data received"}
@frappe.whitelist()
def get_biometric_details(punch_type):
    biometric_records = frappe.get_all("Biometric", fields=["employee_code", "punch_time", "punch_type", "raw_data"], order_by="creation desc", limit=20, filters={"punch_type":punch_type})
    return biometric_records
