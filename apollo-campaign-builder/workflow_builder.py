"""
Apollo Workflow Builder — DATA FILE

Read by the apollo-campaign-builder skill. Contains the 4 workflow definitions
and browser execution guide. This file is not executed — there is no CLI.

Workflows in Apollo trigger automatic actions when a contact's disposition
changes. They must be created AFTER sequences — each play references a
specific client sequence by name.
"""

# ------------------------------------------------------------------
# Data model
# ------------------------------------------------------------------
# Each workflow:
#   trigger: the Apollo disposition that fires the workflow
#   actions: ordered list of steps Apollo takes automatically

WORKFLOWS = {
    1: {
        "name": "{client} - Disposition: Meeting Scheduled",
        "trigger": {
            "type": "Disposition Change",
            "disposition": "Meeting Scheduled",
            "description": "Fires when an SDR marks a contact as 'Meeting Scheduled' after booking on a call"
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
            {
                "type": "Update Contact Stage",
                "stage": "Meeting Pending",
                "note": "Meeting is booked — objective is now show-up and confirmation"
            },
        ]
    },
    2: {
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
            {
                "type": "Update Contact Stage",
                "stage": "Activated Lead",
                "note": "Interested but no meeting yet — follow-up sequence takes over"
            },
        ]
    },
    3: {
        "name": "{client} - Disposition: Connect Incomplete",
        "trigger": {
            "type": "Disposition Change",
            "disposition": "Connect Incomplete",
            "description": "Fires when an SDR marks a contact as 'Connect Incomplete' — reached but call dropped or cut short"
        },
        "actions": [
            {
                "type": "Add to Sequence",
                "sequence": "{client} - Cold Follow-Up",
                "note": "CRITICAL: must point to THIS client's Cold Follow-Up sequence"
            },
            {
                "type": "Update Contact Stage",
                "stage": "Approaching",
                "note": "Still in the dialing/cadence world — stage stays Approaching"
            },
        ]
    },
    4: {
        "name": "{client} - Disposition: Nurture",
        "trigger": {
            "type": "Disposition Change",
            "disposition": "Nurture",
            "description": "Fires when an SDR marks a contact as 'Nurture' — good fit but timing is later (30+ days)"
        },
        "actions": [
            {
                "type": "Add to Sequence",
                "sequence": "{client} - Nurture",
                "note": "CRITICAL: must point to THIS client's Nurture sequence"
            },
            {
                "type": "Update Contact Stage",
                "stage": "Nurture",
                "note": "Good fit, timing is later — sets stage for long-term follow-up visibility"
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
  - You need the exact sequence names (e.g. "Acme Corp - Activated Lead")
  - Substitute {client} with the actual client name throughout
  - The following contact stages must exist in the Apollo account:
      "Meeting Pending", "Activated Lead", "Approaching", "Nurture"
    (These are set up during apollo-account-setup — confirm before building workflows)
  - The deal pipeline must have an "Activated Lead" deal stage — Workflow 2's
    Create Deal action sets it. This is a custom pipeline stage (not an Apollo
    default, not created by apollo-account-setup). If it's missing, the deal
    stage dropdown has nothing to select and the workflow stays in Draft.

For EACH workflow in WORKFLOWS (1–4):

  STEP A — Navigate and create
    - Go to: https://app.apollo.io/#/workflows
    - Click "New workflow" (top-right)
    - Page navigates to: app.apollo.io/#/workflows/new
    - Canvas opens with "When this happens" trigger area and a "Trigger" config panel on the right

  STEP B — Rename the workflow
    - The workflow auto-names to "New workflow - [timestamp]"
    - Click the title at the top-left to rename it
    - Type the full name: e.g. "Acme Corp - Disposition: Meeting Scheduled"
    - Press Enter or click away to confirm

  STEP C — Configure the trigger
    In the right-side "Trigger" panel:
    1. Select "Based on a trigger event" radio button
    2. "This workflow will target" — leave as "People" (default)
    3. Under "Trigger when":
       a. Click the "Event *" dropdown → select "Contact updated"
       b. A "Field" dropdown appears → click it → search "stage" → select "Contact stage"
       c. A "New value" row appears with "is any of" + a stage picker
       d. Click the stage picker → search or scroll to find the disposition value:
            Workflow 1 → "Meeting Scheduled"
            Workflow 2 → "Activated Lead"
            Workflow 3 → "Connect Incomplete"
            Workflow 4 → "Nurture"
       e. Click the stage name to select it (it appears as a tag in the picker)
    4. Click "Done" (bottom-right of the Trigger panel)

  STEP D — Add actions (in order)
    Right panel now shows an "Actions" palette:
      Integrations | Manage Sequences | Manage lists | Manage deals |
      Assign manual tasks | Update contact/account | Send Notifications | Send webhook

    For each action in workflow["actions"]:

    "Add to Sequence":
      - Click "Manage Sequences" in the Actions palette
      - Block auto-appends after current last block
      - Click the block → config panel slides in from the right
      - Under "Sequence", click "Select..." dropdown
      - Type the client sequence name to search
      - Click the matching result to select it
      - VERIFY the selected name includes the client name — wrong sequence = contacts in wrong campaign

    "Create Deal":
      - Click "Manage deals" in the Actions palette
      - Click the "+" button to insert after the last block
      - Block drops. Click to configure.
      - In config panel: action = "Create a deal", set Deal Stage to action["deal_stage"]

    "Associate Contact to Deal":
      - Click "Manage deals" again → placement mode
      - Click "+" after the Create Deal block
      - Block drops. Click to configure.
      - In config panel: select "Associate contact to deal" action

    "Add to List":
      - Click "Manage lists" in the Actions palette
      - Block auto-appends onto canvas
      - Click block → config panel
      - Enter or select list name from action["list_name"]
      - If the list doesn't exist yet, it will be created on first enrollment

    "Update Contact Stage":
      - Click "Update contact/account" in the Actions palette
      - Block auto-appends onto canvas
      - Click block → config panel
      - Select "Contact" as the object type (if prompted)
      - Find "Contact Stage" field → set value to action["stage"]
      - Confirm and close

  STEP E — Save and activate
    - Click "Launch workflow" button (top-right, yellow/green)
    - Workflow status changes from "Draft" to "Active"
    - Confirm it shows as active at app.apollo.io/#/workflows

  STEP F — Verify
    After creating all 4, spot-check each workflow:
    - Correct trigger disposition
    - Sequence name in "Add contacts to sequence" block contains the client name
    - Contact stage value matches workflow["actions"] stage entry

KNOWN UI DETAILS:
  - "Contact updated" is the trigger event (NOT "Disposition changed")
  - Apollo calls it "Contact stage", not "Disposition" — they mean the same thing in the trigger
  - "Manage Sequences" and "Manage lists" auto-append blocks
  - "Manage deals" uses placement mode (click + to insert)
  - Available stages depend on what's configured in the Apollo account — run apollo-account-setup first

CRITICAL CHECKS BEFORE ACTIVATING:
  - Workflow 1: sequence shows "{client} - Pending Meeting", stage = "Meeting Pending"
  - Workflow 2: sequence shows "{client} - Activated Lead", stage = "Activated Lead"
  - Workflow 3: sequence shows "{client} - Cold Follow-Up", stage = "Approaching"
  - Workflow 4: sequence shows "{client} - Nurture", stage = "Nurture"
"""
