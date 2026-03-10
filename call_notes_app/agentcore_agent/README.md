# AWS AI/ML Q&A Agent — AgentCore Deployment

This agent answers AWS AI/ML questions detected during live calls.
It uses Strands Agent with MCP tool integration to search real AWS documentation.

## MCP Servers Integrated

- **aws-documentation-mcp-server** — Search and read AWS documentation pages (spawned via `uvx`, stdio transport)
- **aws-knowledge-mcp-server** — AWS knowledge base search, regional availability checks (HTTP streamable transport)

The agent spawns these MCP servers internally — no AgentCore Gateway needed.

## Prerequisites

- AWS CLI configured with credentials
- Python 3.12+
- `uv` installed (for `uvx` command): `pip install uv`
- AgentCore CLI: `pip install bedrock-agentcore-starter-toolkit`

## Local Testing (No AgentCore Needed)

You can test the agent locally before deploying:

```bash
cd call_notes_app/agentcore_agent
pip install -r requirements.txt
python agent.py
```

Then in another terminal (on Windows, use PowerShell):
```powershell
curl -X POST http://localhost:8080/invocations `
  -H "Content-Type: application/json" `
  -d '{"prompt":"What is Amazon Bedrock AgentCore?"}'
```

## Deploy to AgentCore Runtime

### 1. Install the AgentCore CLI
```bash
pip install bedrock-agentcore-starter-toolkit
```

### 2. Configure
```bash
cd call_notes_app/agentcore_agent
agentcore configure --entrypoint agent.py --non-interactive --region us-east-1
```

### 3. Deploy
```bash
agentcore launch
```

### 4. Test

On Windows PowerShell, avoid spaces in the JSON to prevent quoting issues:
```powershell
agentcore invoke '{"prompt":"hello"}'
```

For longer prompts, assign to a variable first:
```powershell
$payload = '{"prompt":"What is Amazon Bedrock AgentCore?"}'
agentcore invoke $payload
```

### 5. Check status
```bash
agentcore status --verbose
```

Note the `agentRuntimeArn` — you'll need it for the desktop app integration.

### 6. Wire into the desktop app

In `call_notes_app/agent_client.py`, set the runtime ARN:
```python
AGENTCORE_RUNTIME_ARN = "arn:aws:bedrock-agentcore:us-east-1:ACCOUNT_ID:runtime/AGENT_ID"
```

The client connects via WebSocket with SigV4 auth using your local AWS credentials.

## Architecture

```
Live Transcript
    ↓
Question Detector (regex: AWS keywords + question patterns)
    ↓
Agent Client (agent_client.py)
    ├── Mode 1: AgentCore Runtime (WebSocket + SigV4 auth)
    ├── Mode 2: Local Strands + MCP (spawns uvx MCP servers in-process)
    └── Mode 3: Direct Bedrock (simple Claude call, no tools)
         ↓
    Strands Agent (Claude on Bedrock)
        ├── aws-docs MCP → search_documentation, read_documentation
        └── aws-knowledge MCP → search_documentation, get_regional_availability
         ↓
    Synthesized Answer → UI "AI Answers" Panel
```

## Desktop App Integration

The desktop app (`app.py`) has three fallback levels:

1. If `AGENTCORE_RUNTIME_ARN` is set → connects to deployed agent via WebSocket
2. If `strands-agents` + `mcp` are installed locally → runs agent in-process with MCP tools
3. Otherwise → direct Bedrock `invoke_model` call (no doc search, just Claude's knowledge)

For the full MCP experience locally, install:
```bash
python -m pip install strands-agents mcp
```

## Cleanup

To tear down the deployed agent:
```bash
agentcore destroy
```
