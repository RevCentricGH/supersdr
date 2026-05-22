"""
Apollo Workflow Builder — DATA FILE

Read by the apollo-campaign-builder skill. The skill loads WORKFLOWS and
EXECUTION_GUIDE as Python constants, then drives the Apollo UI via the
Claude in Chrome MCP tools. This file is not executed — there is no CLI.

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
Validated via dry run on 2026-05-20. These steps match the live Apollo UI exactly.

Prerequisites:
  - All 7 sequences must already be created for this client
  - You need the exact sequence names (e.g. "Acme Corp - Activated Lead")
  - Substitute {client} with the actual client name throughout
  - "Meeting Booked" must exist as a Contact Stage in the client's Apollo account
    (it is a custom stage — confirm it's been added before building workflow 3)

For EACH workflow in WORKFLOWS (1–3):

  STEP A — Navigate and create
    - Go to: https://app.apollo.io/#/workflows
    - Click "New workflow" (top-right)
    - Page navigates to: app.apollo.io/#/workflows/new
    - Canvas opens with "When this happens" trigger area and a "Trigger" config panel on the right

  STEP B — Rename the workflow
    - The workflow auto-names to "New workflow - [timestamp]"
    - Click the title at the top-left to rename it
    - Type the full name: e.g. "Acme Corp - Disposition: Activated Lead"
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
            Workflow 1 → "Activated Lead"
            Workflow 2 → "Nurture"
            Workflow 3 → "Meeting Booked"
       e. Click the stage name to select it (it appears as a tag in the picker)
    4. Click "Done" (bottom-right of the Trigger panel)
    - Canvas now shows the trigger block with detail text:
      "Contact updated: Contact stage field changed to [Stage Name]"

  STEP D — Add actions (in order)
    Right panel now shows an "Actions" palette:
      Integrations | Manage Sequences | Manage lists | Manage deals |
      Assign manual tasks | Update contact/account | Send Notifications | Send webhook

    For each action in workflow["actions"]:

    "Add to Sequence":
      - Click "Manage Sequences" in the Actions palette
      - An "Add contacts to sequence" block drops onto the canvas (auto-appended after current last block)
      - Click the block → config panel slides in from the right
      - Under "Sequence", click the "Select..." dropdown
      - Type the client sequence name to search (e.g. "Acme Corp - Activated Lead")
      - Click the matching result to select it
      - VERIFY the selected name includes the client name — wrong sequence = contacts in wrong campaign
      - Click away or press Done to confirm

    "Create Deal":
      - Click "Manage deals" in the Actions palette
      - Banner appears: "Add block: Click the + icon in your workflow to choose where to add the block"
      - Click the "+" button where you want to insert (bottom of the chain = after last block)
      - Block drops. Click it to configure.
      - In config panel: action = "Create a deal", set Deal Stage to action["deal_stage"]

    "Associate Contact to Deal":
      - Click "Manage deals" again → placement mode
      - Click "+" after the Create Deal block
      - Block drops. Click to configure.
      - In config panel: select "Associate contact to deal" action

    "Add to List":
      - Click "Manage lists" in the Actions palette
      - Block drops onto canvas (auto-appended)
      - Click block → config panel
      - Enter or select list name from action["list_name"]
      - If the list doesn't exist yet, it will be created on first enrollment

  STEP E — Rename (if not done in Step B)
    - Click the workflow title in the header and update it now if skipped earlier

  STEP F — Save and activate
    - Click "Launch workflow" button (top-right, yellow/green)
    - Workflow status changes from "Draft" to "Active"
    - Confirm it shows as active in the workflows list at app.apollo.io/#/workflows

  STEP G — Verify
    After creating all 3, check the workflows list:
    - All 3 are present and active
    - Spot-check each: click into the workflow detail and confirm the sequence name
      in the "Add contacts to sequence" block contains the client name

KNOWN UI DETAILS:
  - "Contact updated" is the trigger event (NOT "Disposition changed" — that option doesn't exist)
  - Apollo calls it "Contact stage", not "Disposition" — they mean the same thing
  - "Manage Sequences" auto-appends the block; "Manage deals" uses placement mode (click + to insert)
  - The sequence config panel slides in from the right — it may be off-screen at small window widths;
    use the ref-based find tool to interact with the "Sequence" combobox directly if needed
  - Available stages depend on what's configured in the client's Apollo account;
    Required contact stages that must exist: "Activated Lead", "Nurture", "Meeting Booked"

CRITICAL CHECKS BEFORE ACTIVATING:
  - Workflow 1: sequence picker shows "{client} - Activated Lead" (not another client)
  - Workflow 2: sequence picker shows "{client} - Nurture"
  - Workflow 3: sequence picker shows "{client} - Pending Meeting" AND list is "{client} - Meetings Booked"
"""


