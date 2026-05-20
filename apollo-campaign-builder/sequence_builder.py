"""
Apollo Sequence Builder
-----------------------
Data model for all 7 standard sequences.

This file is NOT run directly. It is read by the apollo-campaign-builder skill,
which uses Claude in Chrome MCP tools to execute each sequence in the Apollo UI.

Usage (via skill):
  The skill reads SEQUENCES and EXECUTION_GUIDE, then drives the browser
  through each sequence creation using vision + DOM interaction tools.

Direct reference:
  python3 sequence_builder.py --list          # print all sequences
  python3 sequence_builder.py --sequence 1    # print one sequence
"""

# ------------------------------------------------------------------
# Data model
# ------------------------------------------------------------------

SEQUENCES = {
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
Validated via dry run on 2026-05-20. These steps match the live Apollo UI exactly.

Before starting:
  1. Confirm Chrome is open and logged in at app.apollo.io
  2. Confirm client name — sequences will be named "{client} - Sequence Name"

For EACH sequence in SEQUENCES (1–7):

  STEP A — Navigate and create
    - Go to: https://app.apollo.io/#/sequences
    - Click "Create sequence" button (top-right, yellow)
    - Modal appears with 4 options: AI-assisted / Templates / Clone / From scratch
    - Click "From scratch"
    - "New Sequence" modal appears with:
        - Sequence Name input (focused, empty)
        - Schedule dropdown (default: Normal Business Hours, Mon-Fri 8AM-5PM — leave as-is)
        - Back / Create buttons
    - Type the full sequence name: e.g. "Acme Corp - Call Only"
    - Click "Create"
    - Page redirects to the steps editor for the new sequence
    - URL becomes: app.apollo.io/#/sequences/{id}
    - Tab title shows the sequence name

  STEP B — Add step 1
    - Steps editor shows "Your sequence is empty" with "+ Add a step" button
    - Click "+ Add a step"
    - An inline dropdown appears (NOT a modal) with these options:
        "Automatic email"
        "Manual email"
        "Phone call"
        "Action item"
        "LinkedIn - send connection request"
        "LinkedIn - send message"
        "LinkedIn - view profile"
        "LinkedIn - interact with post"
    - Click the matching option for step["type"]:
        "Phone Call"      → "Phone call"
        "Manual Email"    → "Manual email"
        "Automatic Email" → "Automatic email"
        "Action Item"     → "Action item"
    - Step is added immediately and its edit panel expands below
    - For step 1 only: set timing to "immediately"
        - A timing pill appears above the step: "Schedules task immediately with due date in 30 minutes"
        - Click the pencil icon on that pill
        - Popup shows two radio options:
            (o) Immediately after contact is added
            ( ) Execute step after [30] [minutes]
        - Select "Immediately after contact is added"
        - Click "Save"
    - Click "Save changes" (top-right button) to persist

  STEP C — Add steps 2 through N
    For each subsequent step:

    1. Scroll to bottom of steps list — "+ Add a step" button is always at the bottom
    2. Click "+ Add a step" → inline dropdown appears
    3. Click the matching step type
    4. Step is added. Now set its timing:
        - A timing pill appears BETWEEN the previous step and this new step
        - Default is "Schedules task immediately with due date in 3 days"
        - Click the pencil icon on that timing pill
        - Popup shows:
            ( ) Immediately after previous step is completed
            (o) Execute step after [3] [days ▼]
        - For unit change: click the unit dropdown → shows "minutes" / "hours" / "days"
        - Set the correct value and unit from step["delay"] and step["unit"]:
            unit == "immediately" → select "Immediately after previous step is completed"
            unit == "minutes"     → set value, select "minutes"
            unit == "hours"       → set value, select "hours"
            unit == "days"        → set value, select "days"
        - Click "Save" on the timing popup
    5. Repeat for all remaining steps
    6. Click "Save changes" after adding all steps

  STEP D — Verify step count
    - Step counter in top-left shows "N steps"
    - Must match len(sequence["steps"])
    - If wrong, do not continue — stop and report

  STEP E — Activate the sequence
    - "Activate" toggle is in the top-right header bar
    - Click it to activate
    - Confirm it switches to active state

  STEP F — Record the sequence ID
    - URL contains: app.apollo.io/#/sequences/{id}
    - Note the ID for workflow setup

After all 7 sequences:
  - Report completion table: name | steps | status
  - Pass sequence name→ID map to workflow_builder.py

KNOWN UI DETAILS:
  - "..." menu on a sequence only shows Clone / Archive — no Delete
  - Timing pills sit between steps on a vertical connector line, not inside the step panel
  - Timing popup closes after clicking Save — no page reload needed
  - Step count in header updates immediately when a step is added
"""


# ------------------------------------------------------------------
# CLI for local reference
# ------------------------------------------------------------------

def print_sequence(num: int, client: str = "ClientName"):
    seq = SEQUENCES[num]
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
        for num in SEQUENCES:
            print_sequence(num, client)
    else:
        print("Usage:")
        print("  python3 sequence_builder.py --list [--client 'Acme Corp']")
        print("  python3 sequence_builder.py --sequence 1 [--client 'Acme Corp']")
