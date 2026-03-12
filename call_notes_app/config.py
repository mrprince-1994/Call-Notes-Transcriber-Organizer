import os

# AWS settings — uses your default AWS credentials (env vars, ~/.aws/credentials, or IAM role)
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

# Audio settings
SAMPLE_RATE = 16000  # Amazon Transcribe expects 16kHz for best results
CHANNELS = 1

# Notes output directory — your personal call notes
NOTES_BASE_DIR = r"C:\Users\mrprince\OneDrive - amazon.com\mrprince SMB WE - Documents\Call Notes"

# SA Specialist SA note directories
SANGHWA_NOTES_DIR = r"C:\Users\mrprince\amazon.com\Reddy, Chandra - SMB Team Folder\Customer Docs\Sanghwa Customer Docs"
AYMAN_NOTES_DIR   = r"C:\Users\mrprince\amazon.com\Reddy, Chandra - SMB Team Folder\Customer Docs\Ayman Customer Docs"

# Claude model IDs on Bedrock
CLAUDE_MODEL_ID = "us.anthropic.claude-sonnet-4-6"

# AgentCore Runtime ARNs
AGENTCORE_RUNTIME_ARN = os.environ.get(
    "AGENTCORE_RUNTIME_ARN",
    "arn:aws:bedrock-agentcore:us-east-1:086680834992:runtime/agent-2LqhjC2fKE"
)
RETRIEVAL_AGENT_ARN = os.environ.get(
    "RETRIEVAL_AGENT_ARN",
    "arn:aws:bedrock-agentcore:us-east-1:086680834992:runtime/agent-2LqhjC2fKE"
)
RESEARCH_AGENT_ARN = os.environ.get(
    "RESEARCH_AGENT_ARN",
    "arn:aws:bedrock-agentcore:us-east-1:086680834992:runtime/researchagent-4i3Uyh3OJh"
)
