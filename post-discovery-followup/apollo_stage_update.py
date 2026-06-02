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
# These are LOGICAL stage labels. The operator's own Apollo pipeline may use
# different exact stage names, so the target stage is confirmed against their
# pipeline at the confirmation step (STEP D). Nothing is hardcoded to one
# pipeline. If the map changes, change it in outcome-taxonomy.md, not here.


# ------------------------------------------------------------------
# Execution guide (read by the skill agent)
# ------------------------------------------------------------------

EXECUTION_GUIDE = """
APOLLO DEAL-STAGE UPDATE - BROWSER EXECUTION STEPS
==================================================

WHEN THIS RUNS:
  Only on a confirmed `proposal` or `needs_followup` outcome, after the operator
  has reviewed the draft from client-proposal-doc-builder. The other five
  outcomes never reach this guide - they stop and report with no Apollo write.

NO SILENT WRITE (the core rule):
  Never change a stage on a best-guess match. The operator confirms the exact
  opportunity AND the target stage before any write. On zero or multiple
  matches, the operator picks or supplies the opportunity. There is no automatic
  top-match write and no alias table - the operator resolves any name mismatch
  in person at the confirmation step.

Before starting:
  1. Confirm Chrome is open and logged in at app.apollo.io. If it is not, stop
     and ask: "Open Chrome, go to app.apollo.io, log in, then let me know."
  2. Have the company name (the same one passed to client-proposal-doc-builder,
     inferred from the transcript).
  3. Look up the target stage for the confirmed outcome in
     reference/outcome-taxonomy.md (Outcome-to-Apollo-stage map):
       proposal       -> "Proposal Sent"
       needs_followup -> "Follow-up"

STEP A - Navigate to opportunities
  - Use mcp__Claude_in_Chrome__navigate to open:
      https://app.apollo.io/#/opportunities
  - Confirm the opportunities list loaded and the page did not redirect to
    login. If it redirected, stop and ask the operator to log in.

STEP B - Search by company name
  - Search the opportunities list for the company name (use the list search /
    filter box, or the account-name column). Match on the account/company the
    opportunity belongs to, not on the opportunity title alone.
  - Collect every opportunity whose account matches the company name, with its
    current stage and last-activity date.

STEP C - Resolve the match (this is where alias mismatches get fixed)
  Branch on how many opportunities matched:

  - EXACTLY ONE match:
      Carry it to STEP D for confirmation. Do not write yet.

  - ZERO matches:
      Tell the operator no opportunity matched that company name. The name on
      the calendar or in the transcript often differs from the Apollo account
      name (agency vs end-client, campaign alias). Ask the operator to supply
      the opportunity: search again under the name they give, or have them paste
      the opportunity. Do not create a new opportunity. Do not write.

  - MULTIPLE matches:
      List them (opportunity name, account, current stage, last activity) and
      ask the operator to pick the right one. Do not guess and do not write to
      the top match. Carry the chosen opportunity to STEP D.

STEP D - Confirm before any write
  - Show the operator, in one block:
      - the opportunity name and account
      - its CURRENT stage
      - the TARGET stage (the logical label from the map)
  - Ask the operator to confirm the target stage matches a real stage in their
    Apollo pipeline. If their pipeline names it differently (e.g. "Proposal" vs
    "Proposal Sent"), use the operator's exact pipeline stage name.
  - Require an explicit "yes" to proceed. Do not treat "sure", "ok", or "yeah"
    as confirmation. On anything else, stop and write nothing.

STEP E - Flip the stage
  - Open the confirmed opportunity.
  - Find the stage control (the stage dropdown on the opportunity, or the
    pipeline/kanban stage selector) and set it to the confirmed target stage.
  - NOTE: the exact opportunity stage control has not been run end-to-end inside
    Claude Cowork. If the UI differs from this description, screenshot it, adapt,
    and note what you saw in the final report. Do not force a guess.

STEP F - Verify the change took
  - Reload or re-open the opportunity and confirm its stage now reads the target
    stage. Confirm no error toast appeared.
  - If the stage did not change: retry once. If it fails again, screenshot and
    report - do not claim the stage was updated when it was not.

REPORT:
  State the opportunity, the old stage, the new stage, and that the change was
  verified. If the write was skipped (no confirmed match, or the operator
  declined), say so plainly and that no stage was changed.
"""
