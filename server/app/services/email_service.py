"""
Mock Email Service for PRM Tool.
Prints formatted emails to the console instead of sending real SMTP emails.
"""

def send_timesheet_reminder(employee_email: str, name: str, reminder_number: int) -> None:
    """Sends a timesheet reminder (1 or 2)."""
    subject = f"[Action Required] Timesheet Reminder {reminder_number} / 2"
    body = f"""
Hello {name},

This is reminder {reminder_number} of 2. You have not submitted your timesheet for the previous week.
Please log into the PRM tool and submit your timesheet immediately.

Note: After the second reminder, your timesheet access will be frozen and your manager will be notified.

Regards,
PRM Admin
"""
    _mock_send(employee_email, subject, body)


def send_account_frozen_notice(emp_email: str, mgr_email: str, name: str) -> None:
    """Sends a notice that the account is frozen to both the employee and manager."""
    subject = "[Alert] Timesheet Access Frozen due to non-submission"
    body = f"""
Hello {name},

You have missed the timesheet submission deadline and ignored two reminders. 
As a result, your timesheet submission access has been FROZEN. You can still log in and view your timesheets, but you cannot create, update, or submit entries.

Your reporting manager has been copied on this email. 
Only your reporting manager can review the issue and restore your access.

Regards,
PRM Admin
"""
    _mock_send(f"{emp_email}, {mgr_email}", subject, body)


def send_project_at_risk_notice(
    pm_email: str, 
    project_details: str, 
    health_status: str, 
    risk_summary: str, 
    suggested_help: str
) -> None:
    """Sends an AT_RISK notification to the project manager."""
    subject = f"[Urgent] Project Health Alert: AT_RISK"
    body = f"""
Project Details:
{project_details}

Current Health Status: {health_status}

AI Risk Summary:
{risk_summary}

Suggested Help (Based on available skills and bandwidth):
{suggested_help}

Please act quickly to mitigate the identified risks.
"""
    _mock_send(pm_email, subject, body)


def _mock_send(to_email: str, subject: str, body: str):
    """
    Simulates sending an email by printing to standard out.
    """
    print("\n" + "="*60)
    print("MOCK EMAIL DISPATCHED")
    print("="*60)
    print(f"TO:      {to_email}")
    print(f"SUBJECT: {subject}")
    print("-" * 60)
    print(body.strip())
    print("=" * 60)
