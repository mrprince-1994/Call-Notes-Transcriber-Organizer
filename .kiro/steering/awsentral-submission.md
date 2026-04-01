---
inclusion: auto
description: Conventions for end-of-day AWSentral submission (activities, SIFT, opportunity updates)
---

# AWSentral End-of-Day Submission — Conventions

When processing activity_queue and sift_queue JSON files for AWSentral submission, follow these rules:

## Opportunity Details Format

When updating the `opportunityDetails` field on an opportunity:

1. **Prefix every entry with "MP"** (Michael Prince's initials) followed by the date and a dash:
   - Format: `MP {M/D} - {concise summary of the call}`
   - Example: `MP 3/31 - Architecture review: Coach AI hooks and memory working. Two blockers identified...`

2. **Append, never overwrite.** If `opportunityDetails` already has content, add the new dated entry on a new line below the existing text. Only remove older entries if you hit a character limit and need to fit the latest update.

3. **Keep each entry concise** — one to three sentences capturing the key outcome, decisions, and next steps from the call.

## GenAI/ML Tag Selection

- **AGS-Specialist-GenAI/ML-Leading** (`aNgRU0000001t7J0AQ`): Use when the call notes contain clear, defined next steps with SA involvement (e.g., architecture reviews, build sessions, deliverables).
- **AGS-Specialist-GenAI/ML-Supporting** (`aNgRU0000001zsf0AA`): Use when the call was internal-only, advisory, or has no clear SA-driven next steps.
- If the opportunity already has either tag, leave it as-is.

## MEDDPICC Updates

- Only populate MEDDPICC fields that are currently empty — never overwrite existing values.
- Keep each field under 500 characters.
- Only apply to Utility-type opportunities in standard stages (Prospect, Qualified, Technical Validation, Business Validation, Committed).

## Tracker

After creating each task, call `generate_opp_team_tracker.append_opportunity` with the task details.
