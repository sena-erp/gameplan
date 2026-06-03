import frappe


def execute():
	Task = frappe.qb.DocType("GP Task")
	frappe.qb.update(Task).where(Task.status == "Done").set(Task.is_completed, 1).run()
	frappe.qb.update(Task).where(Task.status != "Done").set(Task.is_completed, 0).set(
		Task.completed_at, None
	).set(Task.completed_by, None).run()

	for task in frappe.get_all(
		"GP Task",
		filters={"status": "Done"},
		fields=["name", "completed_at", "completed_by", "modified", "modified_by"],
		limit_page_length=99999,
	):
		values = {}
		if not task.completed_at:
			values["completed_at"] = task.modified
		if not task.completed_by:
			values["completed_by"] = task.modified_by
		if values:
			frappe.db.set_value("GP Task", task.name, values, update_modified=False)
