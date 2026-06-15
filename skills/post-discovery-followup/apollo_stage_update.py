"""
Apollo Deal-Stage Update - DATA FILE

Read by the post-discovery-followup skill on a draft-and-Apollo-write outcome
(`proposal` or `needs_followup`), after the operator has approved the draft.

This file holds the EXECUTION_GUIDE for the Apollo opportunity stage update via
the Apollo REST API: find the opportunity by company name, show the matched
opportunity and its current stage, require explicit operator confirmation, then
update the stage and verify. No browser.

The outcome-to-Apollo-stage map is NOT duplicated here. It lives in
`reference/outcome-taxonomy.md` (the "Outcome-to-Apollo-stage map" table), which
is the single source of truth for triage and Apollo routing. Look up the target
stage for the confirmed outcome there before running this guide. Only `proposal`
and `needs_followup` reach this guide; the other five outcomes stop and report.

This file is not executed - there is no CLI. It is read at runtime as data.
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
# Live example (RevCentric.ai pipeline, dry-run 2026-06-01): the stages were
# Activated Lead, Discovery Booked, Discovery Held, Close Call Booked, Proposal,
# Closed Won, Fridge, Closed Lost, Disqualified, Churned. There, "Proposal Sent"
# is the stage named "Proposal", and there is NO "Follow-up" stage - so on
# needs_followup the operator picks the closest stage or declines (no write).


# ------------------------------------------------------------------
# Execution guide (read by the skill agent)
# ------------------------------------------------------------------

EXECUTION_GUIDE = """
APOLLO DEAL-STAGE UPDATE - APOLLO REST API (no browser)
=======================================================

WHEN THIS RUNS:
  Only on a confirmed `proposal` or `needs_followup` outcome, after the operator
  has reviewed the draft from client-proposal-doc-builder. The other five
  outcomes never reach this guide - they stop and report with no Apollo write.

REQUIRED CAPABILITY:
  An HTTP client bound to the Apollo REST API at api.apollo.io, authenticated
  with the operator's Apollo API key (APOLLO_API_KEY in the environment). If you
  have no HTTP-client capability, or APOLLO_API_KEY is not set, stop and tell the
  operator which is missing. There is no browser or manual-checklist fallback;
  the REST API path is the only path.

NO SILENT WRITE (the core rule):
  Never move a deal on a best-guess match. The operator confirms the exact deal
  AND the target stage before any write. On zero or multiple matches, the
  operator picks or supplies the deal. There is no automatic top-match write and
  no alias table - the operator resolves any name mismatch in the session at the
  confirmation step.

VOCABULARY:
  In the Apollo API an "opportunity" is the deal. Each opportunity carries an
  `opportunity_stage_id` pointing at one pipeline stage. Moving a deal's stage
  means setting that id to the target stage's id.

Before starting:
  1. Confirm an HTTP client is bound to api.apollo.io with APOLLO_API_KEY set.
     If not, stop (see REQUIRED CAPABILITY).
  2. Have the company name (the same one passed to client-proposal-doc-builder,
     inferred from the transcript).
  3. Look up the target stage for the confirmed outcome in
     reference/outcome-taxonomy.md (Outcome-to-Apollo-stage map):
       proposal       -> "Proposal Sent" (logical)
       needs_followup -> "Follow-up"     (logical)
     These are LOGICAL labels. The real pipeline may name them differently or
     not have them at all - the operator confirms the real stage at STEP D.

STEP A - List the pipeline stages
  - Call the Apollo opportunity-stages endpoint to get every stage in the
    operator's pipeline with its id and display name, in order.
  - These names are what the operator sees; the logical label from the map is
    matched against them at STEP D.

STEP B - Find the opportunity by company name
  - Query the Apollo opportunities search endpoint, filtering by the company
    name. Match on the account/company the opportunity belongs to, not on the
    deal title alone - Apollo deal titles often read "<Company> - New Deal".
  - Collect every opportunity whose company matches, with its id, current
    `opportunity_stage_id` (resolved to the stage name from STEP A), and last
    activity / created date.

STEP C - Resolve the match (this is where alias mismatches get fixed)
  - EXACTLY ONE match:
      Carry its id to STEP D for confirmation. Do not update it yet.
  - ZERO matches:
      Tell the operator no opportunity matched that company name. The name on
      the calendar or in the transcript often differs from the Apollo account
      name (agency vs end-client, campaign alias). Ask the operator to supply
      the deal: search again under the name they give, or have them paste the
      opportunity id. Do not create a new opportunity. Do not update anything.
  - MULTIPLE matches:
      List them (deal title, company, current stage, last activity) and ask the
      operator to pick. Do not guess and do not update the first match.

STEP D - Confirm the opportunity AND the real target stage before any write
  - Show the operator, in one block:
      - the deal title and company
      - its CURRENT stage name
      - the TARGET stage (the logical label from the map)
  - Map the logical label to a real stage from STEP A. The label may not exist
    verbatim. In the dry-run pipeline, "Proposal Sent" was the stage named
    "Proposal", and there was no "Follow-up" stage at all. Ask the operator to
    confirm which real stage is the target, and record its stage id.
  - If no stage fits (e.g. needs_followup in a pipeline with no follow-up
    stage), the operator picks the closest stage or declines. On decline, write
    nothing and report that the stage was left unchanged.
  - Require an explicit "yes" to proceed. Do not treat "sure", "ok", or "yeah"
    as confirmation. On anything else, stop and write nothing.

STEP E - Update the opportunity's stage
  - Call the Apollo opportunity-update endpoint for the confirmed opportunity id,
    setting `opportunity_stage_id` to the target stage id from STEP D.
  - On an ambiguous timeout or network failure, do NOT silently re-attempt the
    update - the write may already have succeeded. Tell the operator "update may
    or may not have applied - verify in Apollo directly" and halt. Explicit retry
    is the operator's decision.
  - On a 429 (rate-limited), stop and surface it; do not auto-retry.

STEP F - Verify the update took
  - Re-read the opportunity by its id and confirm its `opportunity_stage_id` now
    equals the target stage id. Match by id, never by name string.
  - If it did not change: report it - do not claim the stage was updated when it
    was not.

REPORT:
  State the deal, the old stage, the new stage, and that the update was verified.
  If the write was skipped (no confirmed match, no fitting stage, or the operator
  declined), say so plainly and that no stage was changed.

ERROR HANDLING (every message shown to the operator):
  Redact APOLLO_API_KEY, authorization headers, request URLs, and raw response
  bodies. Still carry safe diagnostics: sanitized HTTP status, Apollo error
  category if present, the operation name (stages-list, opportunity-search,
  opportunity-update, verify), and the opportunity id when available.
"""
