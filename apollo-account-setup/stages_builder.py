"""
Apollo Contact Stages Builder — DATA FILE

Read by the apollo-account-setup skill. Contains the 11 custom contact stages
and browser execution guide for Settings → Data management →
Objects, fields, stages → Contact fields & stages → Stages.
This file is not executed — there is no CLI.
"""

# ------------------------------------------------------------------
# Data model
# ------------------------------------------------------------------
# Ordered list — build them in this exact sequence top to bottom.

STAGES = [
    "Approaching",
    "Meeting Pending",
    "Activated Lead",
    "Recycle",
    "Referred Outward",
    "New Data Needed",
    "Not in Swimlane",
    "Nurture",
    "Active Client",
    "Meeting Held",
    "Social/Email Only",
]


# ------------------------------------------------------------------
# Execution guide (read by the skill agent)
# ------------------------------------------------------------------

EXECUTION_GUIDE = """
APOLLO CONTACT STAGES SETUP — BROWSER EXECUTION STEPS
======================================================

PERMISSION REQUIREMENT: Adding stages requires an admin/owner permission profile.
  On a restricted seat (e.g. "Call Assistant") the "+ Add Stage" button is disabled.
  Confirm you are on an admin seat before starting.

STEP 1 — Navigate
  - Go to: https://app.apollo.io/#/settings/contacts/stages
  - Nav path: Settings → Data management → "Objects, fields, stages"
              → "Contact fields & stages" → "Stages" tab
  - The stage list is typically NOT empty — Apollo ships a default set. Do not assume
    a clean slate. Check which STAGES entries already exist before adding.

STEP 2 — Add missing stages in order
  For each stage name in STAGES not already present (keep STAGES order):
    a. Click "+ Add Stage" — opens the "New Contact Stage" dialog
    b. Enter the stage name in the "Name" field exactly as written
    c. Leave "Category" on its default "No Category" (other options:
       In Progress / Succeeded / Not Succeeded — not used by this setup)
    d. Click "Create Stage" (the button is labeled "Create Stage", not "Save")
    e. Confirm the stage appears in the list, then continue to the next

  Order matters. Build them top to bottom as listed.

STEP 3 — Verify
  - All 11 stages are present
  - Names match exactly (spelling and capitalization)
  - Order matches STAGES list

CRITICAL RULES:
  - Four stages are required before Apollo Campaign Builder workflows will work:
      "Meeting Pending", "Activated Lead", "Approaching", "Nurture"
    All four are in the STAGES list above. If any are missing, workflows will
    fail to configure correctly.
  - Do NOT delete or rename stages after SDRs start using them — breaks reporting
"""
