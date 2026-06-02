"""
Apollo Deal-Stage Update - DATA FILE

Read by the post-discovery-followup skill on a draft-and-Apollo-write outcome
(`proposal` or `needs_followup`), after the operator has approved the draft.

This file holds the browser EXECUTION_GUIDE for the Apollo opportunity stage
update: search by company name, show the matched opportunity and its current
stage, require explicit operator confirmation, then flip the stage and verify.

The outcome-to-Apollo-stage map is NOT duplicated here. It lives in
`reference/outcome-taxonomy.md` (the "Outcome-to-Apollo-stage map" table), which
is the single source of truth for triage and Apollo routing. Look up the target
stage for the confirmed outcome there before running this guide. Only `proposal`
and `needs_followup` reach this guide; the other five outcomes stop and report.

This file is not executed - there is no CLI.
"""

# ------------------------------------------------------------------
# Outcome-to-stage map
# ------------------------------------------------------------------
# The map is canonical in reference/outcome-taxonomy.md and is read from there.
# For the two outcomes that reach this guide, the logical target stages are:
#   proposal        -> "Proposal Sent"
#   needs_followup  -> "Follow-up"
# These are LOGICAL stage labels. The operator's own Apollo pipeline may name
# the stage differently or not have it at all, so the target stage is confirmed
# against their real pipeline at the confirmation step (STEP D). Nothing is
# hardcoded to one pipeline. If the map changes, change it in
# outcome-taxonomy.md, not here.
#
# Live example (RevCentric.ai pipeline, dry-run 2026-06-01): the columns were
# Activated Lead, Discovery Booked, Discovery Held, Close Call Booked, Proposal,
# Closed Won, Fridge, Closed Lost, Disqualified, Churned. There, "Proposal Sent"
# is the column named "Proposal", and there is NO "Follow-up" column - so on
# needs_followup the operator picks the closest column or declines (no write).


# ------------------------------------------------------------------
# Execution guide (read by the skill agent)
# ------------------------------------------------------------------

EXECUTION_GUIDE = """
APOLLO DEAL-STAGE UPDATE - BROWSER EXECUTION STEPS (KANBAN BOARD)
================================================================

WHEN THIS RUNS:
  Only on a confirmed `proposal` or `needs_followup` outcome, after the operator
  has reviewed the draft from client-proposal-doc-builder. The other five
  outcomes never reach this guide - they stop and report with no Apollo write.

NO SILENT WRITE (the core rule):
  Never move a deal on a best-guess match. The operator confirms the exact deal
  AND the target stage before any write. On zero or multiple matches, the
  operator picks or supplies the deal. There is no automatic top-match write and
  no alias table - the operator resolves any name mismatch in person at the
  confirmation step.

VOCABULARY:
  In the Apollo UI an "opportunity" is a "Deal". The Kanban board lays deals out
  in columns, one column per pipeline stage. Flipping a stage means moving the
  deal's card to the target stage's column. The board is what most operators use.

Before starting:
  1. Confirm Chrome is open and logged in at app.apollo.io. If it is not, stop
     and ask: "Open Chrome, go to app.apollo.io, log in, then let me know."
  2. Have the company name (the same one passed to client-proposal-doc-builder,
     inferred from the transcript).
  3. Look up the target stage for the confirmed outcome in
     reference/outcome-taxonomy.md (Outcome-to-Apollo-stage map):
       proposal       -> "Proposal Sent" (logical)
       needs_followup -> "Follow-up"     (logical)
     These are LOGICAL labels. The real pipeline may name them differently or
     not have them at all - the operator confirms the real column at STEP D.

STEP A - Open the Deals board (Kanban)
  - Use mcp__Claude_in_Chrome__navigate to open https://app.apollo.io/#/deals
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
    handler fires (confirmed in the dry-run). Do not use the global
    "Search across Apollo" box; use the deal-scoped search for this board.
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

STEP D - Confirm the deal AND the real target stage before any write
  - Show the operator, in one block:
      - the deal title and company
      - its CURRENT stage column
      - the TARGET stage (the logical label from the map)
  - Map the logical label to a real column in this pipeline. The label may not
    exist verbatim. In the dry-run pipeline, "Proposal Sent" was the column named
    "Proposal", and there was no "Follow-up" column at all. Ask the operator to
    confirm which real column is the target.
  - If no column fits (e.g. needs_followup in a pipeline with no follow-up
    stage), the operator picks the closest column or declines. On decline, write
    nothing and report that the stage was left unchanged.
  - Require an explicit "yes" to proceed. Do not treat "sure", "ok", or "yeah"
    as confirmation. On anything else, stop and write nothing.

STEP E - Move the deal to the target column
  - On the board, drag the deal's card from its current column to the confirmed
    target stage column. If drag is unreliable, open the deal and set the stage
    from the deal's own stage control, then return to the board.
  - NOTE: this move has NOT been run end-to-end inside Claude Cowork. It writes
    to live data, so validate it on a throwaway test deal, never on a real one.
    If the board differs from this description, screenshot it, adapt, and note
    what you saw. Do not force a guess on a real deal.

STEP F - Verify the move took
  - Confirm the card now sits in the target column and the column counts updated
    (target +1, previous column -1). Confirm no error toast appeared.
  - If it did not move: retry once. If it fails again, screenshot and report -
    do not claim the stage was updated when it was not.

REPORT:
  State the deal, the old stage, the new stage, and that the move was verified.
  If the write was skipped (no confirmed match, no fitting stage, or the operator
  declined), say so plainly and that no stage was changed.
"""
