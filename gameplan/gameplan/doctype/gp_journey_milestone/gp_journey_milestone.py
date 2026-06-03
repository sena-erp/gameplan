# Copyright (c) 2026, Frappe Technologies Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

import gameplan


class GPJourneyMilestone(Document):
	on_delete_set_null = ["GP Task"]

	def before_insert(self):
		if not self.sort_order:
			self.sort_order = get_next_sort_order(self.journey)

	def validate(self):
		self.project = frappe.db.get_value("GP Journey", self.journey, "project")
		if not self.status:
			self.status = "Not Started"

	def after_insert(self):
		self.update_status_from_tasks()

	def on_update(self):
		self.update_linked_tasks_project()

	def update_linked_tasks_project(self):
		for task in frappe.get_all(
			"GP Task",
			filters={"journey_milestone": self.name, "project": ["!=", self.project]},
			pluck="name",
			limit_page_length=999,
		):
			doc = frappe.get_doc("GP Task", task)
			doc.project = self.project
			doc.save()

	def update_status_from_tasks(self):
		active_tasks = frappe.get_all(
			"GP Task",
			filters={"journey_milestone": self.name, "status": ["!=", "Canceled"]},
			fields=["name", "status"],
			limit_page_length=999,
		)
		status = get_status(active_tasks)
		values = {"status": status}

		if status == "Achieved" and self.status != "Achieved":
			values.update({"achieved_at": frappe.utils.now(), "achieved_by": frappe.session.user})
		elif status != "Achieved" and self.status == "Achieved":
			values.update({"achieved_at": None, "achieved_by": None})

		self.db_set(values, update_modified=False)


def get_next_sort_order(journey):
	last_milestone = frappe.get_all(
		"GP Journey Milestone",
		filters={"journey": journey},
		fields=["sort_order"],
		order_by="sort_order desc",
		limit_page_length=1,
	)
	last_sort_order = last_milestone[0].sort_order if last_milestone else 0
	return (last_sort_order or 0) + 1


def get_status(tasks):
	if not tasks:
		return "Not Started"
	if all(task.status == "Done" for task in tasks):
		return "Achieved"
	if any(task.status in ("Todo", "In Progress", "Done") for task in tasks):
		return "In Progress"
	return "Not Started"


def get_permission_query_conditions(user):
	if not user:
		user = frappe.session.user

	if not gameplan.is_guest(user):
		return None

	escaped_user = frappe.db.escape(user)
	return f"""`tabGP Journey Milestone`.project in (
		select `tabGP Guest Access`.project
		from `tabGP Guest Access`
		where `tabGP Guest Access`.user = {escaped_user}
	)"""


def has_permission(doc, ptype="read", user=None):
	user = user or frappe.session.user

	if not gameplan.is_guest(user):
		return True

	return bool(frappe.db.exists("GP Guest Access", {"user": user, "project": doc.project}))
