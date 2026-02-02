// Copyright (c) 2026, neema and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Employee Checkin", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on("Employee Checkin", {
    onload:function(frm){
        if(frm.is_new()){
        let now=frappe.datetime.now_datetime();
        frm.set_value("time",now);
}
    }
})