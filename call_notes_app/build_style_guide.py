"""Read sent Outlook emails and generate a personal writing style guide using Claude.

Run this once (or periodically) to create/update your style guide:
    python build_style_guide.py

The style guide is saved to style_guide.txt and automatically used by the email generator.
"""
import json
import re
import boto3
from botocore.config import Config

# How many recent sent emails to analyze
NUM_EMAILS = 50

ANALYSIS_PROMPT = """You are an expert writing style analyst. I'm going to give you a collection
of emails written by the same person. Analyze their writing style and produce a concise style
guide that could be used to generate new emails that sound like this person wrote them.

Focus on:

1. GREETING STYLE — How do they open emails? (e.g. "Hi team," vs "Hey everyone," vs "Good morning,")
2. TONE — Formal, casual, warm, direct, etc. Give specific examples.
3. SENTENCE STRUCTURE — Short and punchy? Long and detailed? Mix?
4. TRANSITION PHRASES — What words/phrases do they use to connect ideas?
5. CLOSING STYLE — How do they sign off? (e.g. "Best," vs "Thanks," vs "Best regards,")
6. VOCABULARY PATTERNS — Any distinctive words or phrases they use often?
7. FORMATTING HABITS — Do they use bullets, numbered lists, bold, etc.?
8. PARAGRAPH LENGTH — Short paragraphs? Long blocks?
9. ACTION ITEM STYLE — How do they present action items or next steps?
10. OVERALL VOICE — A 2-3 sentence summary of their writing personality.

Output the style guide as plain text instructions that could be appended to an AI prompt
to make it write emails in this person's voice. Be specific and use direct quotes as examples
where possible. Keep it under 500 words.

Here are the emails:

"""

def read_sent_emails(count=NUM_EMAILS):
    """Read recent sent emails from Outlook via COM."""
    import win32com.client
    outlook = win32com.client.Dispatch("Outlook.Application")
    namespace = outlook.GetNamespace("MAPI")
    # 5 = olFolderSentMail
    sent_folder = namespace.GetDefaultFolder(5)
    messages = sent_folder.Items
    messages.Sort("[SentOn]", True)  # newest first

    emails = []
    for i, msg in enumerate(messages):
        if i >= count:
            break
        try:
            body = msg.Body or ""
            # Strip signature block (everything after common signature markers)
            for marker in ["Michael Prince", "Best regards,\n\nMichael", "-- \n"]:
                idx = body.find(marker)
                if idx > 0:
                    body = body[:idx].strip()
                    break
            # Skip very short emails (likely just "thanks" or forwards)
            if len(body.strip()) < 50:
                continue
            # Skip auto-replies and calendar responses
            subject = msg.Subject or ""
            if any(skip in subject.lower() for skip in ["automatic reply", "out of office", "accepted:", "declined:", "tentative:"]):
                continue
            emails.append({
                "subject": subject,
                "body": body.strip()[:2000],  # cap length per email
            })
        except Exception:
            continue

    print(f"Read {len(emails)} sent emails from Outlook")
    return emails


def analyze_style(emails):
    """Send emails to Claude for style analysis."""
    email_text = "\n\n---EMAIL---\n\n".join(
        f"Subject: {e['subject']}\n\n{e['body']}" for e in emails
    )

    client = boto3.client(
        "bedrock-runtime",
        region_name="us-east-1",
        config=Config(read_timeout=300),
    )

    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096,
        "messages": [
            {
                "role": "user",
                "content": ANALYSIS_PROMPT + email_text,
            }
        ],
    }

    print("Analyzing writing style with Claude...")
    response = client.invoke_model(
        modelId="us.anthropic.claude-sonnet-4-6",
        contentType="application/json",
        accept="application/json",
        body=json.dumps(payload),
    )

    result = json.loads(response["body"].read())
    return result["content"][0]["text"]


def main():
    emails = read_sent_emails()
    if not emails:
        print("No emails found. Make sure Outlook is running.")
        return

    style_guide = analyze_style(emails)

    output_path = "style_guide.txt"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(style_guide)

    print(f"\nStyle guide saved to: {output_path}")
    print(f"\n{'='*60}")
    print(style_guide)
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
