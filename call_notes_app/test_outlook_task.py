"""Quick test: create a follow-up task in Outlook for a given customer."""
from transcription.outlook_tasks import create_followup_task

customer = "Quick Suite Internal Ambassadors"
print(f"Attempting to create follow-up task for: {customer}")
result = create_followup_task(customer)
print(f"Result: {'Success' if result else 'Failed — check messages above'}")
