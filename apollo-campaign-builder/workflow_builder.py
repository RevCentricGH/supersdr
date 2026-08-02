"""
Apollo Workflow Builder — DATA FILE

Read by the apollo-campaign-builder skill. Contains the 4 workflow definitions
and browser execution guide. This file is not executed — there is no CLI.

Workflows in Apollo route a contact into a follow-up sequence after a call is
logged with a given disposition. They must be created AFTER sequences — each
play references a specific client sequence by name.

SCOPE: workflows handle SEQUENCE routing only. Contact STAGE changes are handled
by the disposition→stage Triggers built in apollo-account-setup (triggers_builder.py).
Do not add an "Update Contact Stage" action here — it duplicates the trigger and,
when the stage it sets is the same one the workflow watches, re-fires the workflow
against its own output.
"""

# ------------------------------------------------------------------
# Data model
# ------------------------------------------------------------------
# Each workflow:
#   trigger: the "Call logged" event, filtered by source sequence + disposition
#   actions: ordered list of steps Apollo takes automatically

WORKFLOWS = {
    1: {
        "name": "{client} - Disposition: Meeting Scheduled",
        "trigger": {
            "type": "Call Logged",
            "source_sequence": "{client} - Call Only",
            "disposition": "Meeting Scheduled",
            "description": "Fires when an SDR logs a call as 'Meeting Scheduled' after booking on a call"
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
    2: {
        "name": "{client} - Disposition: Activated Lead",
        "trigger": {
            "type": "Call Logged",
            "source_sequence": "{client} - Call Only",
            "disposition": "Activated Lead",
            "description": "Fires when an SDR logs a call as 'Activated Lead' after speaking with them"
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
    3: {
        "name": "{client} - Disposition: Connect Incomplete",
        "trigger": {
            "type": "Call Logged",
            "source_sequence": "{client} - Call Only",
            "disposition": "Connect Incomplete",
            "description": "Fires when an SDR logs a call as 'Connect Incomplete' — reached but call dropped or cut short"
        },
        "actions": [
            {
                "type": "Add to Sequence",
                "sequence": "{client} - Cold Follow-Up",
                "note": "CRITICAL: must point to THIS client's Cold Follow-Up sequence"
            },
        ]
    },
    4: {
        "name": "{client} - Disposition: Nurture",
        "trigger": {
            "type": "Call Logged",
            "source_sequence": "{client} - Call Only",
            "disposition": "Nurture",
            "description": "Fires when an SDR logs a call as 'Nurture' — good fit but timing is later (30+ days)"
        },
        "actions": [
            {
                "type": "Add to Sequence",
                "sequence": "{client} - Nurture",
                "note": "CRITICAL: must point to THIS client's Nurture sequence"
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
  - The following dispositions must exist in the Apollo account:
      "Meeting Scheduled", "Activated Lead", "Connect Incomplete", "Nurture"
    (These are set up during apollo-account-setup Step 3 — confirm before
    building workflows. They are dispositions, not contact stages.)
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
       a. Click the "Event *" dropdown → select "Call logged"
       b. Set the source sequence filter: "in sequence(s)" → select
          trigger["source_sequence"], i.e. "{client} - Call Only".
          This scopes the workflow to calls dialed out of THIS client's
          call sequence. Without it the workflow fires on every logged call
          in the whole workspace, including other clients'.
       c. Set the disposition filter to trigger["disposition"]:
            Workflow 1 → "Meeting Scheduled"
            Workflow 2 → "Activated Lead"
            Workflow 3 → "Connect Incomplete"
            Workflow 4 → "Nurture"
          These are DISPOSITION names, from apollo-account-setup's
          dispositions_builder.DISPOSITIONS. They are not contact stages.
    4. Click "Done" (bottom-right of the Trigger panel)

    VERIFY THE TRIGGER READS BACK CORRECTLY. Switch the canvas to "Detail" view
    and read the "When this happens" card. It must say:
      Call logged with these attributes: in sequence(s) <client> Call Only
      sequence, the disposition <Disposition>
    If the disposition renders as "undefined", the workflow's disposition
    reference is dangling and the workflow will never match. See
    "DANGLING DISPOSITION REFERENCES" below.

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

    NOTE — there is deliberately no "Update Contact Stage" action here.
    Contact stages are moved by the disposition→stage Triggers built in
    apollo-account-setup. Adding a stage action to these workflows duplicates
    that, and re-fires the workflow on its own output when the stage it writes
    is one the workflow watches.

  STEP E — Save and activate
    - Click "Launch workflow" button (top-right, yellow/green)
    - Workflow status changes from "Draft" to "Active"
    - Confirm it shows as active at app.apollo.io/#/workflows

  STEP F — Verify
    After creating all 4, switch each workflow's canvas to "Detail" view and
    spot-check:
    - Trigger event is "Call logged"
    - Trigger card names the correct disposition (not "undefined")
    - Trigger card names this client's Call Only sequence
    - Sequence name in "Add contacts to sequence" block contains the client name

KNOWN UI DETAILS:
  - "Call logged" is the trigger event. There is no "Disposition changed" event.
  - Do NOT use "Contact updated" → "Contact stage". A contact stage is not a
    disposition. Two of the four dispositions these workflows watch
    ("Meeting Scheduled", "Connect Incomplete") do not exist as stages at all,
    so the picker comes up empty and the workflow can never leave Draft.
  - The trigger's disposition list and the Settings → Team dialer → Dispositions
    list are the same objects. The stage list is separate.
  - "Manage Sequences" and "Manage lists" auto-append blocks
  - "Manage deals" uses placement mode (click + to insert)
  - Available dispositions depend on what's configured in the Apollo account —
    run apollo-account-setup first

DANGLING DISPOSITION REFERENCES:
  A workflow stores a reference to the disposition, not its name. Deleting and
  re-creating a disposition (which is exactly what apollo-account-setup Step 3
  does) orphans that reference in every workflow that used it. The workflow
  stays Active, silently matches nothing, and its trigger card renders as
  "the disposition undefined".
  - Run apollo-account-setup ONCE, BEFORE any workflows exist.
  - Never re-run its disposition step on an account that already has workflows.
  - If a workflow shows "undefined", open it, re-select the disposition, save.

WHEN CONTACTS FAIL TO ENROLL:
  "Contact owner does not have email account" on a failed enrollment means the
  contact's owner has no mailbox linked, so a sequence with email steps cannot
  send for them. Link the owner's mailbox (apollo-account-setup Step 1), or
  reassign the contact to an owner who has one.

CRITICAL CHECKS BEFORE ACTIVATING:
  - Workflow 1: disposition "Meeting Scheduled" → sequence "{client} - Pending Meeting"
  - Workflow 2: disposition "Activated Lead"    → sequence "{client} - Activated Lead"
  - Workflow 3: disposition "Connect Incomplete" → sequence "{client} - Cold Follow-Up"
  - Workflow 4: disposition "Nurture"           → sequence "{client} - Nurture"
  - No workflow contains an "Update Contact Stage" action.
"""
