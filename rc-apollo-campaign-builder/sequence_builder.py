"""
Apollo Sequence Builder
-----------------------
Data model for all 7 RC standard sequences.

This file is NOT run directly. It is read by the rc-apollo-campaign-builder skill,
which uses Claude in Chrome MCP tools to execute each sequence in the Apollo UI.

Usage (via skill):
  The skill reads RC_SEQUENCES and EXECUTION_GUIDE, then drives the browser
  through each sequence creation using vision + DOM interaction tools.

Direct reference:
  python3 sequence_builder.py --list          # print all sequences
  python3 sequence_builder.py --sequence 1    # print one sequence
"""

# ------------------------------------------------------------------
# Data model
# ------------------------------------------------------------------

RC_SEQUENCES = {
    1: {
        "name": "Call Only",
        "full_name": "{client} - Call Only",
        "objective": "High-intensity call blitz for fresh leads or fast follow-up cycles.",
        "steps": [
            {"type": "Phone Call",      "delay": 0,  "unit": "immediately"},
            {"type": "Phone Call",      "delay": 3,  "unit": "hours"},
            {"type": "Phone Call",      "delay": 1,  "unit": "days"},
            {"type": "Phone Call",      "delay": 3,  "unit": "hours"},
            {"type": "Phone Call",      "delay": 1,  "unit": "days"},
            {"type": "Phone Call",      "delay": 3,  "unit": "hours"},
            {"type": "Phone Call",      "delay": 1,  "unit": "days"},
            {"type": "Phone Call",      "delay": 3,  "unit": "hours"},
            {"type": "Phone Call",      "delay": 1,  "unit": "days"},
            {"type": "Phone Call",      "delay": 3,  "unit": "hours"},
        ]
    },
    2: {
        "name": "Activated Lead",
        "full_name": "{client} - Activated Lead",
        "objective": "Follow-up with lead who just spoke with an SDR but didn't book.",
        "steps": [
            {"type": "Manual Email",    "delay": 0,  "unit": "immediately",  "note": "Personalized — reference the conversation"},
            {"type": "Phone Call",      "delay": 2,  "unit": "days"},
            {"type": "Automatic Email", "delay": 5,  "unit": "days",         "note": "Automated reminder with CTA to book"},
            {"type": "Phone Call",      "delay": 3,  "unit": "days"},
            {"type": "Phone Call",      "delay": 3,  "unit": "days"},
            {"type": "Phone Call",      "delay": 3,  "unit": "days"},
            {"type": "Phone Call",      "delay": 3,  "unit": "days"},
        ]
    },
    3: {
        "name": "Nurture",
        "full_name": "{client} - Nurture",
        "objective": "Re-engage cold or long-term prospects, light-touch.",
        "steps": [
            {"type": "Manual Email",    "delay": 0,  "unit": "immediately",  "note": "Personalized re-engagement"},
            {"type": "Automatic Email", "delay": 45, "unit": "days",         "note": "Hands-off automated check-in"},
            {"type": "Phone Call",      "delay": 15, "unit": "days"},
            {"type": "Phone Call",      "delay": 3,  "unit": "days"},
            {"type": "Phone Call",      "delay": 3,  "unit": "days"},
            {"type": "Phone Call",      "delay": 3,  "unit": "days"},
            {"type": "Phone Call",      "delay": 15, "unit": "days"},
        ]
    },
    4: {
        "name": "Cold Follow-Up",
        "full_name": "{client} - Cold Follow-Up",
        "objective": "High-frequency blitz for previously unresponsive leads.",
        "steps": [
            {"type": "Phone Call",      "delay": 0,  "unit": "immediately"},
            {"type": "Phone Call",      "delay": 3,  "unit": "hours"},
            {"type": "Phone Call",      "delay": 1,  "unit": "days"},
            {"type": "Phone Call",      "delay": 3,  "unit": "hours"},
            {"type": "Phone Call",      "delay": 1,  "unit": "days"},
            {"type": "Phone Call",      "delay": 3,  "unit": "hours"},
            {"type": "Phone Call",      "delay": 1,  "unit": "days"},
            {"type": "Phone Call",      "delay": 3,  "unit": "hours"},
            {"type": "Phone Call",      "delay": 1,  "unit": "days"},
            {"type": "Phone Call",      "delay": 3,  "unit": "hours"},
            {"type": "Phone Call",      "delay": 1,  "unit": "days"},
            {"type": "Phone Call",      "delay": 3,  "unit": "hours"},
            {"type": "Phone Call",      "delay": 1,  "unit": "days"},
            {"type": "Phone Call",      "delay": 3,  "unit": "hours"},
        ]
    },
    5: {
        "name": "Pending Meeting",
        "full_name": "{client} - Pending Meeting",
        "objective": "Ensure confirmed meetings actually show up.",
        "steps": [
            {"type": "Manual Email",    "delay": 30, "unit": "minutes",      "note": "Confirmation email + meeting instructions"},
            {"type": "Action Item",     "delay": 0,  "unit": "immediately",  "note": "Internal: confirm meeting day before, send confirmation + call day before"},
        ]
    },
    6: {
        "name": "Reschedule",
        "full_name": "{client} - Reschedule",
        "objective": "Rebook missed or cancelled meetings.",
        "steps": [
            {"type": "Phone Call",      "delay": 0,  "unit": "immediately"},
            {"type": "Phone Call",      "delay": 1,  "unit": "days"},
            {"type": "Phone Call",      "delay": 1,  "unit": "days"},
            {"type": "Phone Call",      "delay": 1,  "unit": "days"},
            {"type": "Phone Call",      "delay": 1,  "unit": "days"},
            {"type": "Phone Call",      "delay": 3,  "unit": "days"},
            {"type": "Phone Call",      "delay": 3,  "unit": "days"},
            {"type": "Phone Call",      "delay": 3,  "unit": "days"},
            {"type": "Phone Call",      "delay": 3,  "unit": "days"},
            {"type": "Phone Call",      "delay": 3,  "unit": "days"},
        ]
    },
    7: {
        "name": "Referred To",
        "full_name": "{client} - Referred To",
        "objective": "Reconnect via referral — same cadence as Reschedule.",
        "steps": [
            {"type": "Phone Call",      "delay": 0,  "unit": "immediately"},
            {"type": "Phone Call",      "delay": 1,  "unit": "days"},
            {"type": "Phone Call",      "delay": 1,  "unit": "days"},
            {"type": "Phone Call",      "delay": 1,  "unit": "days"},
            {"type": "Phone Call",      "delay": 1,  "unit": "days"},
            {"type": "Phone Call",      "delay": 3,  "unit": "days"},
            {"type": "Phone Call",      "delay": 3,  "unit": "days"},
            {"type": "Phone Call",      "delay": 3,  "unit": "days"},
            {"type": "Phone Call",      "delay": 3,  "unit": "days"},
            {"type": "Phone Call",      "delay": 3,  "unit": "days"},
        ]
    },
}


# ------------------------------------------------------------------
# Execution guide (read by the skill agent)
# ------------------------------------------------------------------

EXECUTION_GUIDE = """
APOLLO SEQUENCE CREATION — BROWSER EXECUTION STEPS
====================================================

Before starting:
  1. Confirm Apollo is open and logged in at app.apollo.io
  2. Confirm client name is known — sequences will be named "{client} - Sequence Name"

For EACH sequence in RC_SEQUENCES:

  STEP A — Navigate to Sequences
    - Go to: https://app.apollo.io/#/sequences
    - Wait for page to fully load (network idle)
    - Verify you're not redirected to login

  STEP B — Create new sequence
    - Click the "New Sequence" or "Create Sequence" button (top-right area)
    - A modal or inline input will appear asking for the sequence name
    - Type the full name: e.g. "Acme Corp - Call Only"
    - Confirm / click Create
    - Wait for redirect to the sequence steps editor

  STEP C — Add each step (loop through sequence["steps"])
    For each step dict {type, delay, unit}:

    1. Click "Add a step" (button at bottom of steps list)
    2. A modal opens with step type options
    3. Click the matching step type:
         "Phone Call"      → click Phone Call option
         "Manual Email"    → click Manual Email option
         "Automatic Email" → click Automatic Email option
         "Action Item"     → click Action Item / Task option
    4. Set the timing delay:
         unit == "immediately" → leave delay at 0 / default
         unit == "minutes"     → enter delay value, ensure unit is set to "minutes"
         unit == "hours"       → enter delay value, ensure unit is set to "hours"
         unit == "days"        → enter delay value, ensure unit is set to "days"
    5. If step has a "note" field — this is context only, no UI field to fill
    6. Click Save / Add Step to confirm
    7. Wait for the modal to close and the step to appear in the list

  STEP D — Verify step count
    - After all steps are added, count the steps visible in the editor
    - Must match len(sequence["steps"])
    - If count is wrong, do not proceed — flag the discrepancy

  STEP E — Activate the sequence
    - Look for an "Activate" or "Launch" button
    - Click it to set the sequence to active
    - Confirm the sequence status shows as active

  STEP F — Record the sequence URL/ID
    - The URL will contain the sequence ID: app.apollo.io/#/sequences/{id}/steps
    - Note this ID — needed for workflow_builder.py

After all 7 sequences are created:
  - Print a completion table showing each sequence name, step count, and status
  - Pass the sequence name→ID mapping to workflow_builder.py
"""


# ------------------------------------------------------------------
# CLI for local reference
# ------------------------------------------------------------------

def print_sequence(num: int, client: str = "ClientName"):
    seq = RC_SEQUENCES[num]
    name = seq["full_name"].format(client=client)
    print(f"\n{'='*60}")
    print(f"Sequence {num}: {name}")
    print(f"Objective: {seq['objective']}")
    print(f"Steps ({len(seq['steps'])}):")
    for i, step in enumerate(seq["steps"], 1):
        timing = "immediately" if step["unit"] == "immediately" else f"+{step['delay']} {step['unit']}"
        note = f"  ← {step['note']}" if "note" in step else ""
        print(f"  {i:>2}. {step['type']:<18} {timing}{note}")


if __name__ == "__main__":
    import sys

    client = "ClientName"
    if "--client" in sys.argv:
        idx = sys.argv.index("--client")
        client = sys.argv[idx + 1]

    if "--sequence" in sys.argv:
        idx = sys.argv.index("--sequence")
        num = int(sys.argv[idx + 1])
        print_sequence(num, client)
    elif "--list" in sys.argv:
        for num in RC_SEQUENCES:
            print_sequence(num, client)
    else:
        print("Usage:")
        print("  python3 sequence_builder.py --list [--client 'Acme Corp']")
        print("  python3 sequence_builder.py --sequence 1 [--client 'Acme Corp']")
