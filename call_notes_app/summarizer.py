import json
import boto3
from config import AWS_REGION, CLAUDE_MODEL_ID

SYSTEM_PROMPT = """You are an expert meeting note-taker. Given a raw transcript of a call,
produce comprehensive, detailed, and well-organized notes. Capture EVERYTHING of substance
from the conversation — do not summarize or condense. Your goal is to create a complete
written record that someone who missed the call could read and be fully up to speed.

Structure the notes as follows:

## Meeting Context
Who was on the call, the purpose, and any relevant background mentioned.

## Detailed Discussion Notes
A thorough, chronological account of what was discussed. Organize by topic with sub-bullets
for details. Include:
- Specific points raised by participants
- Questions asked and answers given
- Technical details, numbers, dates, or specifics mentioned
- Concerns or objections raised
- Examples or scenarios discussed

## Decisions & Agreements
Every decision made or agreement reached, with the reasoning behind it if discussed.

## Action Items & Owners
A numbered list of every action item, who is responsible, and any deadlines mentioned.

## Open Questions & Unresolved Items
Anything that was raised but not resolved, or that needs further investigation.

## Follow-Up & Next Steps
Planned follow-ups, next meetings, or milestones discussed.

## Key Quotes & Verbatim Notes
Any particularly important statements, commitments, or notable quotes worth preserving exactly.

## Additional Context
Background information, references to documents/tools/systems, or anything else
that provides useful context for future reference.

Be exhaustive. It is better to include too much detail than too little. Preserve specifics,
names, numbers, and technical details exactly as stated."""


def generate_notes(transcript: str, customer_name: str) -> str:
    """Send transcript to Claude on Bedrock and return comprehensive organized notes."""
    client = boto3.client("bedrock-runtime", region_name=AWS_REGION)

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 8192,
        "system": SYSTEM_PROMPT,
        "messages": [
            {
                "role": "user",
                "content": (
                    f"Customer/Meeting: {customer_name}\n\n"
                    f"Raw Transcript:\n{transcript}"
                ),
            }
        ],
    })

    response = client.invoke_model(
        modelId=CLAUDE_MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=body,
    )

    result = json.loads(response["body"].read())
    return result["content"][0]["text"]
