// Copyright (c) 2026, neema and contributors
// For license information, please see license.txt


frappe.query_reports["Monthly Leave Summary"] = {
    "filters": [
        {
            "fieldname": "month",
            "label": "Month",
            "fieldtype": "Select",
            "options": [
                { "label": "January", "value": "1" },
                { "label": "February", "value": "2" },
                { "label": "March", "value": "3" },
                { "label": "April", "value": "4" },
                { "label": "May", "value": "5" },
                { "label": "June", "value": "6" },
                { "label": "July", "value": "7" },
                { "label": "August", "value": "8" },
                { "label": "September", "value": "9" },
                { "label": "October", "value": "10" },
                { "label": "November", "value": "11" },
                { "label": "December", "value": "12" }
            ],
            "reqd": 1
        },
        {
            "fieldname": "year",
            "label": "Year",
            "fieldtype": "Int",
            "default": new Date().getFullYear(),
            "reqd": 1
        },
		{
            "fieldname": "leave_type",
            "label": "Leave Type",
            "fieldtype": "Select",
            "options": [
                { "label": "Sick Leave", "value": "Sick Leave" },
                { "label": "Casual Leave", "value": "Casual Leave" },
        
            ]
        }
    ]
};

