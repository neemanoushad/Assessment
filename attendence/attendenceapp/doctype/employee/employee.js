// Copyright (c) 2026, neema and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Employee", {
// 	refresh(frm) {

// 	},
// });



frappe.ui.form.on('Employee', {
     martial_status: function(frm) {
        toggle_spouse_fields(frm);
    },
    refresh:function(frm){
        toggle_spouse_fields(frm);
    },
    first_name:function(frm){
        set_full_name(frm);
    },
    middle_name:function(frm){
        set_full_name(frm);
    },
    last_name:function(frm){
        set_full_name(frm);
    },
    refresh(frm) {
        set_full_name(frm);

    },
    onload(frm) {
        if (!frm.doc.company) {
            frappe.db.get_list('Company', {
                fields: ['name'],
                limit: 1
            }).then(records => {
                if (records.length > 0) {
                    frm.set_value('company', records[0].name);
                }
            });
        }
    }
 
});

function toggle_spouse_fields(frm) {
    if (frm.doc. martial_status === 'Married') {
        frm.set_df_property('spouse_name', 'hidden', 0);  // Show
        frm.set_df_property('spouse_name', 'reqd', 1);    // Make required
    } else {
        frm.set_df_property('spouse_name', 'hidden', 1);  // Hide
        frm.set_df_property('spouse_name', 'reqd', 0);    // Not required
        frm.set_value('spouse_name', '');                 // Clear value
    }
}

function set_full_name(frm) {
    let parts=[];
    if(frm.doc.first_name){
        parts.push(frm.doc.first_name);
    }
    if(frm.doc.middle_name){
        parts.push(frm.doc.middle_name);
    }
    if(frm.doc.last_name){
        parts.push(frm.doc.last_name);
    }
    frm.set_value("full_name", parts.join(" "));
}


