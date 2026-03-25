"""Create a single follow-up Outlook task when a call concludes."""
from datetime import datetime, timedelta


def create_followup_task(customer_name: str) -> bool:
    """Create one 'Follow up - {Customer Name}' task in Outlook To Do. Returns True on success."""
    try:
        import pythoncom
        import win32com.client
    except ImportError:
        print("[outlook_tasks] pywin32 not installed, skipping task creation")
        return False

    try:
        pythoncom.CoInitialize()
    except Exception:
        pass  # Already initialized on main thread

    try:
        outlook = win32com.client.Dispatch("Outlook.Application")
    except Exception as e:
        print(f"[outlook_tasks] Outlook not available: {e}")
        return False

    try:
        task = outlook.CreateItem(3)  # olTaskItem
        task.Subject = f"Follow up - {customer_name}"
        task.Body = (
            f"Follow up with {customer_name} after call.\n\n"
            f"Auto-generated from call notes on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        task.Categories = "Call Notes"
        task.Status = 0  # olTaskNotStarted
        task.Importance = 1  # Normal

        # Due next business day
        due = datetime.now() + timedelta(days=1)
        if due.weekday() == 5:  # Saturday
            due += timedelta(days=2)
        elif due.weekday() == 6:  # Sunday
            due += timedelta(days=1)

        task.DueDate = due.strftime("%m/%d/%Y")
        task.StartDate = datetime.now().strftime("%m/%d/%Y")
        task.ReminderSet = False

        task.Save()
        print(f"[outlook_tasks] Created: Follow up - {customer_name}")
        return True
    except Exception as e:
        print(f"[outlook_tasks] Failed to create task: {e}")
        return False
