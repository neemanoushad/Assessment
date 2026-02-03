frappe.ui.form.on('Leave Application', {
    refresh(frm) {
        if (frm.doc.employee) {
            render_leave_balance(frm);
        }
    },

    after_save(frm) {
        // ✅ ONLY after save, recalc pending
        render_leave_balance(frm);
    },

    from_date(frm) {
        calculate_days(frm);
    },

    to_date(frm) {
        if (frm.doc.from_date && frm.doc.to_date) {
            if (frappe.datetime.get_day_diff(frm.doc.to_date, frm.doc.from_date) < 0) {
                frappe.show_alert({
                    message: __("To Date cannot be before From Date. Resetting to From Date."),
                    indicator: "orange"
                });

                frm.set_value("to_date", frm.doc.from_date);
                return;
            }
        }
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

        if (frappe.datetime.get_day_diff(frm.doc.to_date, frm.doc.from_date) < 0) {
            frappe.msgprint("To Date cannot be earlier than From Date");
            frappe.validated = false;
            return;
        }
    }
});

function calculate_days(frm) {
    if (frm.doc.from_date && frm.doc.to_date) {
        let from = frappe.datetime.str_to_obj(frm.doc.from_date);
        let to = frappe.datetime.str_to_obj(frm.doc.to_date);

        if (to < from) {
            frm.set_value("total_leave_days", 0);
            return;
        }

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
    }
}

function render_leave_balance(frm) {
    if (!frm.doc.employee) return;

    frappe.call({
        method: "attendence.attendenceapp.doctype.leave_application.leave_application.get_leave_balance",
        args: { employee: frm.doc.employee },
        callback(r) {
            if (r.message) {
                let data = r.message;

                // 🚫 Do nothing while NEW (before first save)
                if (frm.is_new()) {
                    let html = frappe.render_template("leave_application", { data: data });
                    frm.dashboard.clear_headline();
                    frm.dashboard.set_headline(html);
                    return;
                }

                // ✅ Only AFTER save
                if (frm.doc.docstatus === 0 && frm.doc.leave_type && frm.doc.total_leave_days) {
                    if (data[frm.doc.leave_type]) {
                        if (frm.doc.status === "Approved") {
                            // Admin saved as Approved → pending = 0
                            data[frm.doc.leave_type].leaves_pending_approval = 0;
                        } else {
                            // Employee saved → pending = total_leave_days
                            data[frm.doc.leave_type].leaves_pending_approval = frm.doc.total_leave_days;
                        }
                    }
                }

                let html = frappe.render_template("leave_application", { data: data });
                frm.dashboard.clear_headline();
                frm.dashboard.set_headline(html);
            }
        }
    });
}
