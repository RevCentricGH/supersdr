"""
Apollo Dispositions Builder — DATA FILE

Read by the apollo-account-setup skill. Contains the 19 custom dispositions
and browser execution guide for Settings → Team Dialer → Dispositions.
This file is not executed — there is no CLI.
"""

# ------------------------------------------------------------------
# Data model
# ------------------------------------------------------------------
# connected: True  = "Connected" — contact will NOT advance in sequence
# connected: False = "Not Connected" — contact WILL advance in sequence

DISPOSITIONS = [
    # CONNECTED / POSITIVE
    {"name": "Meeting Scheduled",               "connected": True,  "sentiment": "Positive"},
    {"name": "Activated Lead",                  "connected": True,  "sentiment": "Positive"},
    # CONNECTED / NEUTRAL
    {"name": "Connect Incomplete",              "connected": True,  "sentiment": "Neutral"},
    {"name": "Referred Outward",                "connected": True,  "sentiment": "Neutral"},
    {"name": "Not Me",                          "connected": True,  "sentiment": "Neutral"},
    {"name": "Not Now",                         "connected": True,  "sentiment": "Neutral"},
    {"name": "Meeting Confirmed",               "connected": True,  "sentiment": "Neutral"},
    {"name": "Meeting Rescheduled",             "connected": True,  "sentiment": "Neutral"},
    {"name": "Connect Incomplete - Follow Up",  "connected": True,  "sentiment": "Neutral"},
    {"name": "Nurture",                         "connected": True,  "sentiment": "Neutral"},
    # CONNECTED / NEGATIVE
    {"name": "Not Interested",                  "connected": True,  "sentiment": "Negative"},
    {"name": "Connect Incomplete - DNC",        "connected": True,  "sentiment": "Negative"},
    {"name": "Bad / Wrong Number",              "connected": True,  "sentiment": "Negative"},
    {"name": "Not in Swimlane",                 "connected": True,  "sentiment": "Negative"},
    {"name": "No Longer with Company",          "connected": True,  "sentiment": "Negative"},
    # NOT CONNECTED
    {"name": "Connect Incomplete - Bad Data",   "connected": False, "sentiment": None},
    {"name": "Left Voicemail",                  "connected": False, "sentiment": None},
    {"name": "Gatekeeper",                      "connected": False, "sentiment": None},
    {"name": "No Answer/Not Available",         "connected": False, "sentiment": None},
]


# ------------------------------------------------------------------
# Execution guide (read by the skill agent)
# ------------------------------------------------------------------

EXECUTION_GUIDE = """
APOLLO DISPOSITIONS SETUP — BROWSER EXECUTION STEPS
=====================================================

BEFORE STARTING: Confirm explicit user approval.
  The skill must have already prompted: "This will delete all existing dispositions
  in your Apollo account. Type 'yes' to continue."
  Do NOT enter this guide until the user has typed 'yes'.

STEP 1 — Navigate (search-box method — resilient to Apollo URL changes)
  - Go to app.apollo.io and click Settings (gear icon, bottom of left sidebar).
  - In the Settings search box, type "dialer".
  - Under "Workspace settings", click "Team dialer".
  - On the Team dialer page, select the "Dispositions" tab
    (tabs: Dispositions | Purposes | Team Numbers | Recording).
  - Confirm the page header reads "Call Dispositions" and a yellow
    "+ Add Disposition" button is visible top-right.
  - Do NOT rely on the hardcoded hash URL /#/settings/dialer — it is stale and
    fails to load the dispositions view. Navigate via the search box instead.
  - Note: the disposition→stage Triggers (set up separately) live at the BOTTOM
    of this same Dispositions page.

STEP 2 — Delete all existing dispositions
  - Delete each existing disposition one by one until the list is empty
  - Confirm the list shows zero entries before proceeding

STEP 3 — Add all 19 dispositions
  For each entry in DISPOSITIONS (in order):
    a. Click "Add Disposition"
    b. Enter the Name field exactly — spelling and capitalization must match
    c. Set "Connected with desired contact?":
         connected == True  → select "Connected"
         connected == False → select "Not Connected"
    d. Set "Call Sentiment" (only shown for Connected dispositions):
         "Positive" / "Neutral" / "Negative" per disposition["sentiment"]
         If the field is hidden (Not Connected entries) — skip it
    e. Click "Save"
    f. Confirm the entry appears in the list before moving to the next

STEP 4 — Verify count
  - Total dispositions shown must equal 19
  - If wrong, identify the missing entry, add it, recheck

CRITICAL RULES:
  - Names must match EXACTLY — one wrong character breaks reporting consistency
  - "Left Voicemail" must be Not Connected — it must keep advancing the sequence
  - Do NOT add any dispositions beyond the 19 listed
  - Do NOT rename dispositions after SDRs start using them
"""
