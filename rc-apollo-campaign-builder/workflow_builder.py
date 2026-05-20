"""
Apollo Workflow Builder
-----------------------
Data model for the 3 RC standard workflow plays.

This file is NOT run directly. It is read by the rc-apollo-campaign-builder skill,
which uses Claude in Chrome MCP tools to execute each workflow in the Apollo UI.

Workflows in Apollo trigger automatic actions when a contact's disposition changes.
They must be created AFTER sequences — each play references a specific client sequence.

Usage (via skill):
  The skill reads RC_WORKFLOWS and EXECUTION_GUIDE, then drives the browser
  through each workflow creation using vision + DOM interaction tools.

Direct reference:
  python3 workflow_builder.py --list
  python3 workflow_builder.py --workflow 1
"""

# ------------------------------------------------------------------
# Data model
# ------------------------------------------------------------------
# Each workflow:
#   trigger: the Apollo disposition that fires the workflow
#   actions: ordered list of steps Apollo takes automatically

RC_WORKFLOWS = {
    1: {
        "name": "{client} - Disposition: Activated Lead",
        "trigger": {
            "type": "Disposition Change",
            "disposition": "Activated Lead",
            "description": "Fires when an SDR marks a contact as 'Activated Lead' after speaking with them"
        },
        "actions": [
            {
                "type": "Add to Sequence",
                "sequence": "{client} - Activated Lead",
                "note": "CRITICAL: must point to THIS client's sequence, not another client's"
            },
            {
                "type": "Create Deal",
                "deal_stage": "Activated Lead",
                "note": "Creates a deal in Apollo CRM at the Activated Lead stage"
            },
            {
                "type": "Associate Contact to Deal",
                "note": "Links the contact to the deal just created"
            },
        ]
    },
    2: {
        "name": "{client} - Disposition: Nurture",
        "trigger": {
            "type": "Disposition Change",
            "disposition": "Nurture",
            "description": "Fires when an SDR marks a contact as 'Nurture' (not ready, re-engage later)"
        },
        "actions": [
            {
                "type": "Add to Sequence",
                "sequence": "{client} - Nurture",
                "note": "CRITICAL: must point to THIS client's sequence"
            },
        ]
    },
    3: {
        "name": "{client} - Disposition: Meeting Booked",
        "trigger": {
            "type": "Disposition Change",
            "disposition": "Meeting Booked",
            "description": "Fires when an SDR marks a contact as 'Meeting Booked'"
        },
        "actions": [
            {
                "type": "Add to List",
                "list_name": "{client} - Meetings Booked",
                "note": "Creates or adds to a static list for tracking booked meetings"
            },
            {
                "type": "Add to Sequence",
                "sequence": "{client} - Pending Meeting",
                "note": "CRITICAL: must point to THIS client's Pending Meeting sequence"
            },
        ]
    },
}


# ------------------------------------------------------------------
# Execution guide (read by the skill agent)
# ------------------------------------------------------------------

EXECUTION_GUIDE = """
APOLLO WORKFLOW CREATION — BROWSER EXECUTION STEPS
====================================================

Prerequisites:
  - All 7 sequences must already be created for this client
  - You need the exact sequence names used (e.g. "Acme Corp - Activated Lead")
  - Substitute {client} with the actual client name throughout

For EACH workflow in RC_WORKFLOWS:

  STEP A — Navigate to Workflows
    - Go to: https://app.apollo.io/#/workflows
    - Wait for page to fully load
    - Click "New Workflow" or "Create Workflow" (top-right)

  STEP B — Set the workflow name
    - Enter the name: e.g. "Acme Corp - Disposition: Activated Lead"

  STEP C — Set the trigger
    Each workflow triggers on a Disposition Change:
    - Look for "Trigger" section or "When this happens..."
    - Select trigger type: "Disposition is updated" or "Contact disposition changes"
    - Set the disposition value to match workflow["trigger"]["disposition"]:
        Workflow 1 → "Activated Lead"
        Workflow 2 → "Nurture"
        Workflow 3 → "Meeting Booked"

  STEP D — Add actions (in order)
    For each action in workflow["actions"]:

    "Add to Sequence":
      - Click "Add action" or "Then do this..."
      - Select "Add to Sequence"
      - In the sequence picker, search for and select:
        the exact client sequence name (e.g. "Acme Corp - Activated Lead")
      - VERIFY the selected sequence name before saving
      - This is the #1 setup error — wrong sequence = contacts going to wrong client

    "Create Deal":
      - Select "Create Deal" action
      - Set Deal Stage to the value in action["deal_stage"]

    "Associate Contact to Deal":
      - Select "Associate to Deal" or similar
      - This links the contact to the deal created in the previous step

    "Add to List":
      - Select "Add to List"
      - Enter or select the list name from action["list_name"]
      - Create the list if it doesn't exist yet

  STEP E — Save and activate
    - Click Save
    - Toggle the workflow to Active
    - Confirm it shows as active in the workflows list

  STEP F — Verify each workflow
    After creating all 3, go back to the workflows list and confirm:
    - All 3 workflows are present and active
    - Sequence names shown in each workflow match the client (spot-check in the workflow detail)

CRITICAL CHECKS BEFORE ACTIVATING:
  - Workflow 1: sequence picker shows "{client} - Activated Lead" (not another client)
  - Workflow 2: sequence picker shows "{client} - Nurture"
  - Workflow 3: sequence picker shows "{client} - Pending Meeting" AND list is "{client} - Meetings Booked"
"""


# ------------------------------------------------------------------
# CLI for local reference
# ------------------------------------------------------------------

def print_workflow(num: int, client: str = "ClientName"):
    wf = RC_WORKFLOWS[num]
    name = wf["name"].format(client=client)
    trigger = wf["trigger"]
    print(f"\n{'='*60}")
    print(f"Workflow {num}: {name}")
    print(f"Trigger: {trigger['type']} → disposition = \"{trigger['disposition']}\"")
    print(f"  ({trigger['description']})")
    print(f"Actions ({len(wf['actions'])}):")
    for i, action in enumerate(wf["actions"], 1):
        atype = action["type"]
        detail = ""
        if "sequence" in action:
            detail = f" → {action['sequence'].format(client=client)}"
        elif "list_name" in action:
            detail = f" → {action['list_name'].format(client=client)}"
        elif "deal_stage" in action:
            detail = f" → stage: {action['deal_stage']}"
        note = f"\n     NOTE: {action['note']}" if "note" in action else ""
        print(f"  {i}. {atype}{detail}{note}")


if __name__ == "__main__":
    import sys

    client = "ClientName"
    if "--client" in sys.argv:
        idx = sys.argv.index("--client")
        client = sys.argv[idx + 1]

    if "--workflow" in sys.argv:
        idx = sys.argv.index("--workflow")
        num = int(sys.argv[idx + 1])
        print_workflow(num, client)
    elif "--list" in sys.argv:
        for num in RC_WORKFLOWS:
            print_workflow(num, client)
    else:
        print("Usage:")
        print("  python3 workflow_builder.py --list [--client 'Acme Corp']")
        print("  python3 workflow_builder.py --workflow 1 [--client 'Acme Corp']")
