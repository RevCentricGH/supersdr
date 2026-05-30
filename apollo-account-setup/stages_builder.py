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
STATUS: PATH/NAV VALIDATED 2026-05-29 (live Apollo UI). Add-stage FORM FIELDS still
        unvalidated — the "+ Add Stage" button is disabled on non-admin seats, so the
        add flow could not be exercised. Re-validate Step 2 on an admin/owner seat.

PERMISSION REQUIREMENT: Adding stages requires an admin/owner permission profile.
  On a restricted seat (e.g. "Call Assistant") the "+ Add Stage" button is disabled.
  Confirm you are on an admin seat before starting.

STEP 1 — Navigate (VALIDATED)
  - Go to: https://app.apollo.io/#/settings/contacts/stages
  - Nav path: Settings → Data management → "Objects, fields, stages"
              → "Contact fields & stages" → "Stages" tab
  - The stage list is typically NOT empty — Apollo ships a default set. Do not assume
    a clean slate. Check which STAGES entries already exist before adding.

STEP 2 — Add missing stages in order (FORM FIELDS UNVALIDATED)
  For each stage name in STAGES not already present (keep STAGES order):
    a. Click "+ Add Stage"
    b. Enter the stage name exactly as written
    c. Save — confirm the stage appears in the list
    d. Continue to the next stage

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
