# Sales Productivity Suite

An AI-powered Windows desktop application for customer-facing sales professionals. Live-transcribes calls, generates structured notes and follow-up emails, provides pre-call prep briefs, auto-fills post-call debrief analytics, and offers cross-customer trend analysis — all powered by AWS services.

Built on Amazon Transcribe, Amazon Bedrock (Claude), and local SQLite storage.

---

## Features

### Tab 1: Live Transcription
- Real-time dual-stream transcription (system audio + mic) via Amazon Transcribe with speaker diarization
- AI-generated comprehensive meeting notes streamed in real-time via Claude on Bedrock
- AI-generated follow-up email draft (runs in parallel with notes)
- Post-call debrief auto-filled from transcript: what went well, risks, next steps
- One-click Outlook draft creation with signature preserved
- Pre-call prep briefs from historical notes (markdown-formatted, streamed)
- Export notes as DOCX or PDF
- Queue SIFT insights and SA activities for AWSentral submission (via Kiro hooks)
- Duplicate detection prevents re-queuing the same call
- Customer name locking during generation prevents accidental overwrites
- Smart transcript auto-scroll (pauses when you scroll up to read)
- Session history stored locally in SQLite

### Tab 2: Notes Retrieval
- Multi-turn chat interface to query across all historical call notes
- Indexes .md and .docx files from multiple directories (your notes + teammate folders)
- Recency-aware retrieval: newest notes are prioritized and presented first
- Year inference for teammate files with MM_DD naming patterns
- Source and customer filters with searchable picker
- Suggested prompts for common queries
- Session history with save/restore/delete
- Powered by Claude Opus 4.6 with tool-use (file reading, web search, AWS docs, pricing)

### Tab 3: Customer Research
- Web-powered research chat for any customer or topic
- Customer Brief Generator: formatted DOCX with company profile, leadership, tech landscape, AWS references, discovery questions, and meeting agenda
- Session history with save/restore/delete

### Tab 4: Trends & Insights
- Call analytics dashboard: 14-day trend, top customers, competitor frequency, sentiment donut
- Stat cards with colored accent bars (total calls, this week, this month, customers, competitors)
- AI-powered trend generation: cross-cutting patterns across all calls with markdown formatting
- Polished dark-themed matplotlib charts

### Automated Features
- Smart Follow-Up Reminders: auto-creates Outlook To Do tasks from action items
- Competitive Intel Extraction: auto-detects competitor mentions, stores in SQLite
- Weekly Digest: summary email every Monday via Windows Task Scheduler
- Email Style Guide: analyzes your sent emails to personalize follow-up tone

### AWSentral Integration (via Kiro Hooks)
- Queue SA activities from call notes for submission to Salesforce
- Queue SIFT leadership insights with debrief-enriched category classification
- Auto-tag opportunities with AGS-Specialist-GenAI/ML-Supporting
- Opportunity team tracker (Excel) auto-updated on each activity submission
- Duplicate detection prevents double-queuing

---

## Prerequisites

- Python 3.10+ (tested with 3.12/3.13)
- Windows (required for VB-CABLE audio routing and Outlook integration)
- AWS Account with Amazon Transcribe and Bedrock (Claude) access
- AWS CLI configured (`aws configure`)
- VB-CABLE virtual audio driver ([download](https://vb-audio.com/Cable/))
- Microsoft Outlook desktop app (for email drafts and tasks)

---

## Installation

```bash
cd call_notes_app
python -m pip install -r requirements.txt
```


## Running the App

```bash
cd call_notes_app
python app.py
```

The app opens with four tabs: Live Transcription, Notes Retrieval, Customer Research, and Trends & Insights.

---

## Quick Start

1. Enter a customer name
2. Select audio devices (System Audio = CABLE Output, Microphone = your mic)
3. Click **Start Recording** — live transcript streams in real-time
4. Click **Stop & Generate** — three things happen in parallel:
   - Claude generates comprehensive structured notes (streamed)
   - Claude generates a follow-up email draft (streamed)
   - Claude auto-fills the post-call debrief (what went well, risk, next step)
5. Review the debrief fields, then click **SIFT** to queue a leadership insight
6. Click **Activity** to queue an SA activity for AWSentral
7. Click **Outlook Draft** to create the email in your Drafts folder

---

## Configuration

All settings are in `config.py`:

| Setting | Description |
|---|---|
| `AWS_REGION` | AWS region for all services (default: `us-east-1`) |
| `NOTES_BASE_DIR` | Where notes and briefs are saved — **change this** |
| `SANGHWA_NOTES_DIR` | Optional teammate notes folder (set to `""` if not needed) |
| `AYMAN_NOTES_DIR` | Optional teammate notes folder (set to `""` if not needed) |
| `CLAUDE_MODEL_ID` | Bedrock model for notes/email generation |
| `RETRIEVAL_AGENT_ARN` | AgentCore ARN or `None` for local mode |
| `RESEARCH_AGENT_ARN` | AgentCore ARN or `None` for local mode |

---

## Project Structure

```
call_notes_app/
├── app.py                        # Main entry point — all 4 tab UIs
├── config.py                     # All configurable settings
├── md_render.py                  # Markdown-to-Tkinter streaming renderer
├── weekly_digest.py              # Weekly summary email (Task Scheduler)
├── backfill_insights.py          # One-time backfill of competitive intel
├── requirements.txt
├── README.md / SETUP.md / AUDIO_SETUP_GUIDE.md
│
├── transcription/                # Tab 1: Live Transcription
│   ├── transcriber.py            # Audio capture + Amazon Transcribe Streaming
│   ├── summarizer.py             # Notes, email, prep, debrief extraction
│   ├── storage.py                # DOCX conversion and file saving
│   ├── history.py                # SQLite session persistence
│   ├── competitive_intel.py      # Competitor mention tracking
│   ├── outlook_tasks.py          # Outlook To Do task creation
│   ├── activity_logger.py        # SA activity extraction + queue (AWSentral)
│   └── sift_insight.py           # SIFT insight extraction + queue (AWSentral)
│
├── retrieval/                    # Tabs 2 & 3
│   ├── notes_retriever.py        # Note indexing, retrieval agent, research agent
│   ├── chat_history.py           # SQLite chat session persistence
│   └── customer_brief.py         # Customer brief generator (DOCX)
│
└── agentcore_agent/              # Deployable AgentCore agents (optional)
    ├── agent.py                  # Strands Agent with MCP tools
    ├── research_agent/           # Customer research agent
    └── retrieval_agent/          # Notes retrieval agent
```

---

## Audio Setup

See [AUDIO_SETUP_GUIDE.md](call_notes_app/AUDIO_SETUP_GUIDE.md) for detailed instructions.

Quick version: Install VB-CABLE → set Windows output to CABLE Input → enable listen-through on CABLE Output → select devices in the app.

---

## Troubleshooting

| Issue | Solution |
|---|---|
| No transcript appearing | Check Windows output is set to CABLE Input; verify device selection |
| Bedrock `AccessDeniedException` | Verify Claude models in Bedrock console; check IAM permissions |
| Outlook draft fails | Ensure Outlook desktop app is running; install `pywin32` |
| No competitors in Insights | Run `python backfill_insights.py` to populate from history |
| Duplicate activity queued | Duplicate detection is automatic — same call won't queue twice |
| Pre-call prep empty | Enter a customer name that matches your note files |
| Notes saved to wrong folder | Customer name is locked when you click Stop — won't change if you click history |
