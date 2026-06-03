# Copyright (c) 2026, Frappe Technologies Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

import gameplan


class GPJourney(Document):
	on_delete_cascade = ["GP Journey Milestone"]

	def validate(self):
		self.validate_one_journey_per_space()

	def validate_one_journey_per_space(self):
		existing = frappe.db.exists("GP Journey", {"project": self.project, "name": ["!=", self.name]})
		if existing:
			frappe.throw("Only one journey can exist for a space.")


@frappe.whitelist()
def get_for_space(space):
	check_space_permission(space)
	journey = frappe.db.get_value(
		"GP Journey",
		{"project": space},
		["name", "title", "description", "project"],
		as_dict=True,
	)
	if not journey:
		return None

	milestones = get_milestones(journey.name)
	tasks = get_tasks([str(milestone.name) for milestone in milestones])
	task_map = build_task_map(tasks)
	milestone_rows = []
	total_required = 0
	total_done = 0

	for milestone in milestones:
		milestone_tasks = task_map.get(str(milestone.name), [])
		active_tasks = [task for task in milestone_tasks if task.status != "Canceled"]
		done_tasks = [task for task in active_tasks if task.status == "Done"]
		total_required += len(active_tasks)
		total_done += len(done_tasks)
		milestone_rows.append(
			{
				**milestone,
				"tasks": milestone_tasks,
				"task_count": len(active_tasks),
				"done_task_count": len(done_tasks),
				"progress": get_progress(len(done_tasks), len(active_tasks)),
			}
		)

	return {
		"journey": journey,
		"milestones": milestone_rows,
		"progress": {
			"task_count": total_required,
			"done_task_count": total_done,
			"percent": get_progress(total_done, total_required),
		},
	}


def get_milestones(journey):
	return frappe.get_all(
		"GP Journey Milestone",
		filters={"journey": journey},
		fields=[
			"name",
			"title",
				"description",
				"lane",
				"start_date",
				"responsible_user",
				"target_date",
			"status",
			"achieved_at",
			"achieved_by",
			"sort_order",
		],
		order_by="sort_order asc, target_date asc, creation asc",
		limit_page_length=999,
	)


def get_tasks(milestones):
	if not milestones:
		return []
	return frappe.get_all(
		"GP Task",
		filters={"journey_milestone": ["in", milestones]},
		fields=[
			"name",
			"title",
			"status",
			"priority",
				"assigned_to",
				"start_date",
				"due_date",
			"project",
			"journey_milestone",
		],
		order_by="idx asc, creation asc",
		limit_page_length=999,
	)


def build_task_map(tasks):
	task_map = {}
	for task in tasks:
		task_map.setdefault(str(task.journey_milestone), []).append(task)
	return task_map


def get_progress(done, total):
	if not total:
		return 0
	return round(done * 100 / total)


def check_space_permission(space):
	project = frappe.get_doc("GP Project", space)
	project.check_permission("read")


def get_permission_query_conditions(user):
	if not user:
		user = frappe.session.user

	if not gameplan.is_guest(user):
		return None

	escaped_user = frappe.db.escape(user)
	return f"""`tabGP Journey`.project in (
		select `tabGP Guest Access`.project
		from `tabGP Guest Access`
		where `tabGP Guest Access`.user = {escaped_user}
	)"""


def has_permission(doc, ptype="read", user=None):
	user = user or frappe.session.user

	if not gameplan.is_guest(user):
		return True

	return bool(frappe.db.exists("GP Guest Access", {"user": user, "project": doc.project}))
