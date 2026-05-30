"""
Apollo Triggers Builder — DATA FILE

Read by the apollo-account-setup skill. Contains the disposition→stage trigger
map and browser execution guide. Triggers auto-flip a contact's contact stage
when a call is dispositioned — they handle STAGE changes (campaign-builder
workflows handle SEQUENCE routing). They live at the bottom of the
Settings → Team Dialer → Dispositions page.
This file is not executed — there is no CLI.

ORDER: build triggers AFTER both dispositions and stages exist. A trigger
references a disposition (source) and a stage (target); both must already be
created or the trigger cannot be saved.
"""

# ------------------------------------------------------------------
# Data model
# ------------------------------------------------------------------
# Each entry maps one disposition (from dispositions_builder.DISPOSITIONS) to
# the contact stage (from stages_builder.STAGES) the contact moves to when that
# disposition is logged. One trigger per disposition — all 19 are mapped.
# Disposition and stage names must match those two builders EXACTLY.

TRIGGERS = [
    # → Meeting Pending
    {"disposition": "Meeting Scheduled",              "stage": "Meeting Pending"},
    {"disposition": "Meeting Confirmed",              "stage": "Meeting Pending"},
    {"disposition": "Meeting Rescheduled",            "stage": "Meeting Pending"},
    # → Activated Lead
    {"disposition": "Activated Lead",                 "stage": "Activated Lead"},
    # → Approaching (Not Connected + incomplete-connect outcomes keep dialing)
    {"disposition": "Connect Incomplete",             "stage": "Approaching"},
    {"disposition": "Connect Incomplete - Follow Up", "stage": "Approaching"},
    {"disposition": "Connect Incomplete - Bad Data",  "stage": "Approaching"},
    {"disposition": "Gatekeeper",                     "stage": "Approaching"},
    {"disposition": "No Answer / Not Available",      "stage": "Approaching"},
    {"disposition": "Left Voicemail",                 "stage": "Approaching"},
    # → Referred Outward
    {"disposition": "Referred Outward",               "stage": "Referred Outward"},
    {"disposition": "Not Me",                         "stage": "Referred Outward"},
    # → Nurture
    {"disposition": "Not Now",                        "stage": "Nurture"},
    {"disposition": "Nurture",                        "stage": "Nurture"},
    {"disposition": "Not Interested",                 "stage": "Nurture"},
    # → Social/Email Only
    {"disposition": "Connect Incomplete - DNC",       "stage": "Social/Email Only"},
    # → New Data Needed
    {"disposition": "Bad / Wrong Number",             "stage": "New Data Needed"},
    # → Not in Swimlane
    {"disposition": "Not in Swimlane",                "stage": "Not in Swimlane"},
    # → Recycle
    {"disposition": "No Longer with Company",         "stage": "Recycle"},
]


# ------------------------------------------------------------------
# Execution guide (read by the skill agent)
# ------------------------------------------------------------------

EXECUTION_GUIDE = """
APOLLO TRIGGERS SETUP — BROWSER EXECUTION STEPS
=================================================

PRECONDITION: All 19 dispositions and all 11 contact stages must already exist.
  A trigger maps an existing disposition to an existing stage — build this step
  LAST, after Steps 3 (dispositions) and 4 (stages).

STEP 1 — Navigate
  - Go to the same page as dispositions: Settings → search "dialer" →
    Team dialer → "Dispositions" tab.
  - Scroll to the BOTTOM of the Dispositions page to the Triggers section
    (the disposition→stage automation lives here, not on the Stages page).

STEP 2 — Add one trigger per entry in TRIGGERS
  For each entry in TRIGGERS (order does not matter — one per disposition):
    a. Add a new trigger.
    b. Set the source disposition to entry["disposition"] (must match an
       existing disposition name exactly).
    c. Set the resulting contact stage to entry["stage"] (must match an
       existing stage name exactly).
    d. Save — confirm the trigger appears in the list.

STEP 3 — Verify
  - 19 triggers total, one per disposition.
  - Every disposition in dispositions_builder.DISPOSITIONS has exactly one
    trigger; no disposition is left unmapped.
  - Spot-check: "Meeting Scheduled" → "Meeting Pending",
    "Left Voicemail" → "Approaching", "Bad / Wrong Number" → "New Data Needed".

CRITICAL RULES:
  - Triggers change the contact STAGE. Campaign-builder workflows change the
    SEQUENCE. Build both or the lifecycle will not move correctly.
  - Disposition and stage names must match the other two builders exactly —
    a mismatch means the trigger silently targets nothing.
"""
