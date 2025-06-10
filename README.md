# CRM Task Automation

CRM Task Automation is a custom Frappe application that automatically creates and assigns tasks when the status of a CRM Lead changes. It supports round-robin or load-balanced distribution of tasks based on configurable rules.

## Features

- Define **Lead Task Config** records to map lead statuses to tasks.
- Create tasks automatically when a lead transitions to a configured status.
- Assign tasks to users based on territory, industry, or a **Task Assignment Rule**.
- Supports round robin or load balancing strategies for assignment.

## Installation

This app is designed to be installed in a Frappe/ERPNext site using Bench:

```bash
bench get-app crm_task_automation <app_path>
bench --site <your-site> install-app crm_task_automation
```

## License

This project is released under the MIT License. See `license.txt` for details.
