import frappe
from frappe.utils import nowdate, add_days
import json

def get_user_round_robin(eligible_users, last_user):
    """
    Get next user based on round robin
    """

    # first time, or last in list, pick the first
    if not last_user or last_user == eligible_users[-1].user:
        return eligible_users[0].user

    # find out the next user in the list
    for i, d in enumerate(eligible_users):
        if last_user == d.user:
            return eligible_users[i + 1].user

    # bad last user, assign to the first one
    return eligible_users[0].user
 
def get_user_load_balancing(eligible_users):
    """
    Assign to the user with the least number of open tasks
    """
    counts = [
        dict(
            user=d.user,
            count=frappe.db.count(
                "ToDo",
                dict(
                    reference_type='CRM Task',
                    allocated_to=d.user,
                    status="Open",
                ),
            ),
        )
        for d in eligible_users
    ]
    
    # sort users based on task count
    sorted_counts = sorted(counts, key=lambda k: k["count"])

    # return the user with the least open tasks
    return sorted_counts[0].get("user")

def get_user(assignment_rule_doc, lead_doc):
    """
    Get the next user for assignment
    """
    assignment_conditions = json.loads(assignment_rule_doc.condition) if assignment_rule_doc.condition else {}
    rule = assignment_rule_doc.rule
    eligible_users = assignment_rule_doc.users
    last_user = assignment_rule_doc.last_user

    if assignment_rule_doc.disabled:
        return None  
        
    if rule == "Round Robin":
        selected_assignee = get_user_round_robin(eligible_users, last_user)
        print("selected_assignee", selected_assignee)

        # Check if the lead matches the condition
        if all(str(lead_doc.get(key)) == str(value) for key, value in assignment_conditions.items()):
            frappe.db.set_value('Task Assignment Rule', assignment_rule_doc.name, 'last_user', selected_assignee)
            return selected_assignee

    elif rule == "Load Balancing":
        selected_assignee = get_user_load_balancing(eligible_users)
        print("selected_assignee", selected_assignee)

        # Check if the lead matches the condition
        if all(str(lead_doc.get(key)) == str(value) for key, value in assignment_conditions.items()):
            return selected_assignee
 

def get_assigned_user(lead_doc, assigned_to, assignment_rule):
    # Check for Territory Manager
    if assigned_to == 'Based On territory':
        if lead_doc.territory:
            territory_manager = frappe.db.get_value("CRM Territory", lead_doc.territory, "territory_manager")
            if territory_manager:
                return territory_manager

    # Check for Industry Responsable
    if assigned_to == 'Based On industry':
        if lead_doc.industry:
            industry_responsable = frappe.db.get_value("CRM Industry", lead_doc.industry, "custom_responsable")
            if industry_responsable:
                return industry_responsable

    if assigned_to == 'Based On Rule':
        if assignment_rule:
            assignment_rule_doc = frappe.get_doc("Task Assignment Rule", assignment_rule)

            selected_assignee = get_user(assignment_rule_doc, lead_doc)
            return selected_assignee

    return None


def create_task_based_on_status(doc, method):    
    # Fetch all tasks associated with the given lead status
    if doc.get_doc_before_save() and doc.get_doc_before_save().status != doc.status:
        task_configs = frappe.get_all(
            "Lead Task Config",
            filters={"lead_status": doc.status},
            fields=["task_title", "assigned_to", "assignment_rule", "due_in", "priority", "status", "description", "active"]
        )

        if not task_configs:
            return 

        for task_config in task_configs:
            if not task_config.get("active"):
                continue  
            
            task_title = task_config.get("task_title")
            assigned_to = task_config.get("assigned_to")
            due_in_days = task_config.get("due_in", 0)  
            priority = task_config.get("priority", "Medium")
            status = task_config.get("status", "Open")
            description = task_config.get("description")
            assignment_rule = task_config.get("assignment_rule")

            # Determine the assigned user
            determined_assignee = get_assigned_user(doc, assigned_to, assignment_rule) if assigned_to else None

            if determined_assignee:
                final_assignee = determined_assignee
            elif doc.lead_owner:
                final_assignee = doc.lead_owner
            else:
                final_assignee = frappe.session.user 

            # Calculate due date
            due_date = add_days(nowdate(), due_in_days) if due_in_days is not None else nowdate()

            # Validate required fields before task creation
            if task_title and final_assignee:
                task = frappe.get_doc({ 
                    "doctype": "CRM Task",
                    "title": task_title,
                    "status": status,
                    "assigned_to": final_assignee,
                    "priority": priority,
                    "start_date": nowdate(),
                    "due_date": due_date,
                    "reference_document_type": "CRM Lead",
                    "reference_docname": doc.name,
                    "description": description
                })
                task.insert(ignore_permissions=True)
                frappe.db.commit() 

            
            