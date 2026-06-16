"""
Apollo Onboarding-Stage Update - DATA FILE

Read by the onboarding-kickoff skill after the welcome email is sent (or its
send is reported as failed), to move the just-paid client's deal to the
onboarding stage.

This file holds the browser EXECUTION_GUIDE for one move: search the deal by
company name, show the matched deal and its current stage, require explicit
operator confirmation, then move the deal to the onboarding stage and verify.

The skill carries its own copy of this guide rather than importing
post-discovery-followup's, because skills ship as standalone ZIPs. The flow is
the same search-and-confirm flow, trimmed to the single onboarding move.

This file is not executed - there is no CLI.
"""

# ------------------------------------------------------------------
# Target stage
# ------------------------------------------------------------------
# The deal moves to the onboarding stage. "Onboarding" is a LOGICAL label.
# The operator's own Apollo pipeline may name the stage differently, keep
# onboarding in a separate pipeline, or not have a dedicated column. So the
# real target column is confirmed against their pipeline at the confirmation
# step (STEP D). Nothing is hardcoded to one pipeline.
#
# Live example (RevCentric.ai pipeline, dry-run 2026-06-01): the columns were
# Activated Lead, Discovery Booked, Discovery Held, Close Call Booked, Proposal,
# Closed Won, Fridge, Closed Lost, Disqualified, Churned. There, a paid client
# sits in Closed Won and onboarding is tracked outside this pipeline - so the
# operator either points at the right onboarding column or declines (no write).


# ------------------------------------------------------------------
# Execution guide (read by the skill agent)
# ------------------------------------------------------------------

EXECUTION_GUIDE = """
APOLLO ONBOARDING-STAGE UPDATE - BROWSER EXECUTION STEPS (KANBAN BOARD)
======================================================================

WHEN THIS RUNS:
  After the welcome email step in onboarding-kickoff, for a client who has paid.
  It moves that client's deal to the onboarding stage. It runs whether the email
  sent or its send failed; it does NOT run if the run halted for no recipient.

NO SILENT WRITE (the core rule):
  Never move a deal on a best-guess match. The operator confirms the exact deal
  AND the target stage before any write. On zero or multiple matches, the
  operator picks or supplies the deal. There is no automatic top-match write and
  no alias table - the operator resolves any name mismatch in person at the
  confirmation step.

VOCABULARY:
  In the Apollo UI an "opportunity" is a "Deal". The Kanban board lays deals out
  in columns, one column per pipeline stage. Moving a stage means moving the
  deal's card to the target stage's column. The board is what most operators use.

Before starting:
  1. Confirm Chrome is open and logged in at app.apollo.io. If it is not, stop
     and ask: "Open Chrome, go to app.apollo.io, log in, then let me know."
  2. Have the company name (the same client passed through onboarding-kickoff,
     from the operator or the closing-call transcript).
  3. The target stage is the onboarding stage. This is a LOGICAL label - the real
     pipeline may name it differently or track onboarding elsewhere. The operator
     confirms the real column at STEP D.

STEP A - Open the Deals board (Kanban)
  - Navigate to https://app.apollo.io/#/deals in Chrome
    (the older #/opportunities path redirects here).
  - Switch to the board: in the left nav it is Win deals -> Deals; choose the
    "Board view of Deals" (the Kanban view). When a single pipeline is shown the
    URL gains an opportunityPipelineIds[] parameter.
  - Confirm the board loaded and did not redirect to login. If it redirected,
    stop and ask the operator to log in.
  - Confirm the right pipeline is shown (pipeline picker at the top, e.g.
    "All Pipelines"). The board columns are the pipeline stages, left to right.

STEP B - Find the deal by company name
  - Type the company name into the board's deal search/filter. Use real
    keystrokes - a pasted/scripted value will NOT filter unless the input
    handler fires. Do not use the global "Search across Apollo" box; use the
    deal-scoped search for this board.
  - Match on the company the deal belongs to (the Company column), not on the
    deal title alone. Apollo deal titles often read "<Company> - New Deal".
  - Collect every deal whose company matches, with its current stage column and
    last activity / created date.

STEP C - Resolve the match (this is where alias mismatches get fixed)
  - EXACTLY ONE match:
      Carry it to STEP D for confirmation. Do not move it yet.
  - ZERO matches:
      Tell the operator no deal matched that company name. The name on the
      calendar or in the transcript often differs from the Apollo account name
      (agency vs end-client, campaign alias). Ask the operator to supply the
      deal: search again under the name they give, or have them point to the
      card. Do not create a new deal. Do not move anything.
  - MULTIPLE matches:
      List them (deal title, company, current stage column, last activity) and
      ask the operator to pick. Do not guess and do not move the top match.

STEP D - Confirm the deal AND the real onboarding column before any write
  - Show the operator, in one block:
      - the deal title and company
      - its CURRENT stage column
      - the TARGET stage (the logical onboarding label)
  - Map the onboarding label to a real column in this pipeline. The label may not
    exist verbatim, and a paid client often sits in Closed Won with onboarding
    tracked elsewhere. Ask the operator which real column is the onboarding target.
  - If no column fits (the pipeline has no onboarding stage), the operator picks
    the closest column or declines. On decline, write nothing and report that the
    stage was left unchanged.
  - Require an explicit "yes" to proceed. Do not treat "sure", "ok", or "yeah"
    as confirmation. On anything else, stop and write nothing.

STEP E - Move the deal to the onboarding column
  - On the board, drag the deal's card from its current column to the confirmed
    onboarding column. If drag is unreliable, open the deal and set the stage
    from the deal's own stage control, then return to the board.
  - NOTE: Apollo's board drag-and-drop needs native pointer input. If a drag does
    not register, fall back to the deal's own stage control, or screenshot and
    report. This step writes live data, so validate it on a throwaway test deal,
    never on a real one.

STEP F - Verify the move took
  - Confirm the card now sits in the onboarding column and the column counts
    updated (target +1, previous column -1). Confirm no error toast appeared.
  - If it did not move: retry once. If it fails again, screenshot and report -
    do not claim the stage was updated when it was not.

REPORT:
  State the deal, the old stage, the new (onboarding) stage, and that the move
  was verified. If the write was skipped (no confirmed match, no fitting column,
  or the operator declined), say so plainly and that no stage was changed.
"""
