frappe.ui.form.on('Leave Application', {
    refresh(frm) {
        if (frm.doc.employee) {
            render_leave_balance(frm);
        }
    },

    from_date(frm) {
    // ✅ NEW: auto set to_date same as from_date if empty or smaller
    if (!frm.doc.to_date || frm.doc.to_date < frm.doc.from_date) {
        frm.set_value("to_date", frm.doc.from_date);
    }

    calculate_days(frm);
},

    to_date(frm) {
        calculate_days(frm);
    },

    employee(frm) {
        render_leave_balance(frm);
    },

    half_day(frm) {
        calculate_days(frm);
    },

  validate(frm) {
    if (!frm.doc.employee || !frm.doc.leave_type || !frm.doc.from_date || !frm.doc.to_date) return;

    
    frappe.call({
        method: "frappe.client.get_list",
        args: {
            doctype: "Leave Application",
            filters: [
                ["employee", "=", frm.doc.employee],
                ["name", "!=", frm.doc.name],
                ["docstatus", "<", 2],  // draft or submitted
                ["from_date", "<=", frm.doc.to_date],
                ["to_date", ">=", frm.doc.from_date]
            ],
            fields: ["name"]
        },
        async: false,
        callback(r) {
            if (r.message && r.message.length > 0) {
                frappe.msgprint(
                    __(`Employee ${frm.doc.employee} already has a leave applied for the selected date range.`)
                );
                frappe.validated = false; 
            }
        }
    });

    if (!frappe.validated) return;

  
    frappe.call({
        method: "attendence.attendenceapp.doctype.leave_application.leave_application.get_leave_balance",
        args: {
            employee: frm.doc.employee
        },
        async: false,
        callback(r) {
            if (r.message) {
                let row = r.message[frm.doc.leave_type];

                if (!row) {
                    frappe.msgprint(`No Leave Allocation found for Leave Type ${frm.doc.leave_type}`);
                    frappe.validated = false;
                    return;
                }

                let remaining = row.remaining_leaves || 0;

                if (frm.doc.total_leave_days > remaining) {
                    frappe.msgprint(
                        `Insufficient leave balance for ${frm.doc.leave_type}. Remaining: ${remaining}`
                    );
                    frappe.validated = false;
                }
            }
        }
    });
}

});

function calculate_days(frm) {
    if (frm.doc.from_date && frm.doc.to_date) {
        let from = frappe.datetime.str_to_obj(frm.doc.from_date);
        let to = frappe.datetime.str_to_obj(frm.doc.to_date);

        let diff = frappe.datetime.get_day_diff(to, from) + 1;
        if (diff < 0) diff = 0;
        if (frm.doc.half_day) {
           
            if (frm.doc.from_date === frm.doc.to_date) {
                diff = 0.5;
            } else {
                frappe.msgprint("Half Day can be selected only for single day leave");
                frm.set_value("half_day", 0);
            }
        }

        frm.set_value("total_leave_days", diff);

        render_leave_balance(frm);
    }
}

function render_leave_balance(frm) {
    if (!frm.doc.employee) return;

    frappe.call({
        method: "attendence.attendenceapp.doctype.leave_application.leave_application.get_leave_balance",
        args: {
            employee: frm.doc.employee
        },
        callback(r) {
            if (r.message) {
                let html = frappe.render_template("leave_application", {
                    data: r.message
                });

               
                frm.dashboard.clear_headline();
                frm.dashboard.set_headline(html);
            }
        }
    });
}
