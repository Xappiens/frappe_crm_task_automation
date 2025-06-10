// Copyright (c) 2025, Suman and contributors
// For license information, please see license.txt

frappe.ui.form.on("Task Assignment Rule", {
    refresh: function (frm) {
		frm.events.rule(frm);
	},
    
	rule: function (frm) {
		const description_map = {
			"Round Robin": __("Assign one by one, in sequence"),
			"Load Balancing": __("Assign to the one who has the least assignments"),
		};
		frm.get_field("rule").set_description(description_map[frm.doc.rule]);
	},
});
