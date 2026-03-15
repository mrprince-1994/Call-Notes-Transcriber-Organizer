"""Weekly Digest — summarizes all calls from the past 7 days and creates an Outlook draft.

Run manually:
    python weekly_digest.py

Or schedule via Windows Task Scheduler to run every Monday at 7 AM.
See SETUP.md for Task Scheduler instructions.
"""
import json
import sys
import os
from datetime import datetime, timedelta
import boto3
from botocore.config import Config

# Add parent dir to path so config imports work
sys.path.insert(0, os.path.dirname(__file__))
from config import AWS_REGION, CLAUDE_MODEL_ID
from transcription.history import list_sessions

DIGEST_PROMPT = """You are a sales productivity assistant generating a weekly activity digest.
Given notes from all calls in the past week, produce a concise weekly summary email.

Structure it as follows:

Week of {date_range}

CALLS THIS WEEK ({count} total)
List each customer met, with a one-line summary of the call purpose/outcome.

KEY DECISIONS & OUTCOMES
The most important decisions, agreements, or outcomes across all calls this week.

OPEN ACTION ITEMS
All outstanding action items across all customers, grouped by customer.
Include owner and deadline if mentioned.

FOLLOW-UPS DUE
Any follow-ups that were promised or scheduled.

PIPELINE HIGHLIGHTS
Notable opportunities, risks, or momentum shifts worth flagging.

Keep it scannable — short bullets, not paragraphs. This is a Monday morning
5-minute read. Do NOT use markdown formatting (no **, ##, etc.).
Use plain text with dashes for bullets."""


def get_past_week_sessions():
    """Get all sessions from the past 7 days."""
    all_sessions = list_sessions()  # returns all, sorted by timestamp desc
    cutoff = (datetime.now() - timedelta(days=7)).isoformat()
    return [s for s in all_sessions if s.get("timestamp", "") >= cutoff]


def generate_digest(sessions):
    """Send sessions to Claude and get a weekly digest."""
    if not sessions:
        return None

    now = datetime.now()
    week_start = (now - timedelta(days=7)).strftime("%B %d")
    week_end = now.strftime("%B %d, %Y")
    date_range = f"{week_start} - {week_end}"

    combined = "\n\n---\n\n".join(
        f"Customer: {s.get('customer_name', 'Unknown')}\n"
        f"Date: {s.get('timestamp', '')[:16]}\n"
        f"Notes:\n{s.get('notes', '(no notes)')}"
        for s in sessions
    )

    prompt = DIGEST_PROMPT.replace("{date_range}", date_range).replace("{count}", str(len(sessions)))

    client = boto3.client(
        "bedrock-runtime", region_name=AWS_REGION,
        config=Config(read_timeout=300),
    )

    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096,
        "system": prompt,
        "messages": [{
            "role": "user",
            "content": f"Here are all the call notes from the past week:\n\n{combined}",
        }],
    }

    response = client.invoke_model(
        modelId=CLAUDE_MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(payload),
    )

    result = json.loads(response["body"].read())
    return result["content"][0]["text"]


def create_outlook_draft(digest_text):
    """Create an Outlook draft with the weekly digest."""
    import re

    # Parse subject if present
    lines = digest_text.split("\n", 2)
    now = datetime.now()
    week_start = (now - timedelta(days=7)).strftime("%m/%d")
    week_end = now.strftime("%m/%d")
    subject = f"Weekly Call Digest — {week_start} to {week_end}"
    body = digest_text

    # Convert to HTML
    html_lines = []
    lines_list = body.split("\n")
    i = 0
    while i < len(lines_list):
        stripped = lines_list[i].strip()
        if not stripped:
            html_lines.append('<br>')
            i += 1
            continue
        if stripped.startswith("- "):
            bullets = []
            while i < len(lines_list) and lines_list[i].strip().startswith("- "):
                bullets.append(lines_list[i].strip()[2:])
                i += 1
            bullet_html = "".join(f'<li style="margin:0;padding:0;">{b}</li>' for b in bullets)
            html_lines.append(f'<ul style="margin:0 0 0 24px;padding:0;">{bullet_html}</ul>')
        elif len(stripped) < 60 and not stripped.endswith(".") and not stripped.endswith(","):
            html_lines.append(f'<p style="margin:0;"><b>{stripped}</b></p>')
            i += 1
            while i < len(lines_list) and not lines_list[i].strip():
                i += 1
        else:
            html_lines.append(f'<p style="margin:0;">{stripped}</p>')
            i += 1

    html_body = (
        '<div style="font-family:Aptos,Calibri,sans-serif;font-size:11pt;color:#1a1a1a;line-height:1.5;">'
        + "\n".join(html_lines) + "</div>"
    )

    import win32com.client
    outlook = win32com.client.Dispatch("Outlook.Application")
    mail = outlook.CreateItem(0)
    mail.Subject = subject
    mail.To = "mrprince@amazon.com"
    mail.Display()
    mail.HTMLBody = html_body + mail.HTMLBody
    mail.Send()
    print(f"Weekly digest sent to mrprince@amazon.com: {subject}")


def main():
    print("Generating weekly digest...")
    sessions = get_past_week_sessions()
    print(f"Found {len(sessions)} sessions from the past 7 days")

    if not sessions:
        print("No calls this week — skipping digest.")
        return

    digest = generate_digest(sessions)
    if not digest:
        print("Failed to generate digest.")
        return

    print("Sending weekly digest...")
    try:
        create_outlook_draft(digest)
        print("Done! Digest sent.")
    except Exception as e:
        # If Outlook isn't available, save to file instead
        from config import NOTES_BASE_DIR
        fallback_dir = os.path.join(NOTES_BASE_DIR, "_Weekly Digests")
        os.makedirs(fallback_dir, exist_ok=True)
        fallback = os.path.join(fallback_dir, f"weekly_digest_{datetime.now().strftime('%Y-%m-%d')}.txt")
        with open(fallback, "w", encoding="utf-8") as f:
            f.write(digest)
        print(f"Outlook not available ({e}). Saved to: {fallback}")


if __name__ == "__main__":
    main()
