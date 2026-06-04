---
name: post-discovery-followup
description: Run the post-discovery-call workflow inside Cowork with the operator present. Trigger this skill when the user shares a discovery-call transcript (pasted text or a Drive, Gemini, or Fireflies link) and wants the next step after the call, or says things like "I just got off a discovery call", "here's the call transcript", "triage this call", "what's the outcome of this call", or "run post-discovery follow-up". The skill reads the full transcript, proposes one of seven call outcomes with one line of reasoning, and waits for the operator to confirm or override before anything else happens. It then branches on the confirmed outcome per the outcome taxonomy: some outcomes hand off to the client-proposal-doc-builder skill for a draft and then update Apollo, while the rest report the manual next step and stop with no draft and no Apollo write.
---

# Post-Discovery Follow-up

A Cowork skill that reproduces the useful part of the post-discovery workflow with the
operator in the session. The operator shares a discovery-call transcript. The skill reads it,
proposes the call outcome and one line of reasoning, and lets the operator confirm or
override. On a draft outcome it chains into `client-proposal-doc-builder` for the proposal or
follow-up email, sends it through the Gmail connector, and updates the deal stage in Apollo.
On the other outcomes it reports the outcome and the manual next step and stops.

The whole path runs in one Cowork session. The transcript, the company name, the confirmed
outcome, the returned draft, and the recipient carry forward from step to step with no manual
stitching. The skill uses connectors only - Google Drive, Gmail, and Claude-in-Chrome for
Apollo - with no server, no cron, and no local API keys. Every external action (the email send
and the Apollo write) waits for the operator's explicit approval.

This file is the orchestrator. The outcome definitions, the classification criteria, the
outcome-to-Apollo-stage map, and the draft-vs-report branching live in one place:
`reference/outcome-taxonomy.md`. Read that file when you classify and when you branch. Do not
restate its contents here.

## Getting started

When the skill loads, greet the operator:

> "I run the post-discovery follow-up. Share the discovery-call transcript and I'll read it,
> propose the call outcome, and wait for your call before anything goes out.
>
> Paste the transcript, or give me a Google Drive, Gemini, or Fireflies link. Either works."

Wait for the transcript before doing anything else.

## Step 1 - Intake the transcript

Accept the transcript in either form:

- **Pasted text.** Use the pasted block as the transcript.
- **A link** to a Google Drive doc, a Gemini transcript, or a Fireflies transcript. Fetch the
  full document content from the link first, using the Google Drive connector for Drive links
  or browser automation for Gemini and Fireflies links. Do not classify off the link, the
  title, or a preview. Retrieve the whole document, then treat the retrieved text as the
  transcript.

If the link cannot be retrieved, stop and tell the operator which link failed and ask them to
paste the text instead. Never classify from a transcript you could not read.

## Step 2 - Read the transcript in full

Read the entire transcript before you classify. No sampling, no skimming the first and last
few lines, no stopping once you think you know the outcome. This applies the same way to
pasted text and to content retrieved from a link. The outcome and every later step are only
as good as a full read.

## Step 3 - Classify and propose the outcome

Load `reference/outcome-taxonomy.md`. Match the full transcript against its classification
criteria and pick the single best-fit outcome from the seven values it defines: `proposal`,
`needs_followup`, `closed_won`, `closed_lost`, `fridge`, `disqualified`, `stay_in_proposal`.

Present the proposed outcome with exactly one line of reasoning, then stop and wait:

> "Proposed outcome: **needs_followup**
> Reasoning: They want this but need the VP of Sales to sign off before pricing, so the next
> step is a follow-up, not a proposal.
>
> Confirm, or tell me the right outcome."

Then wait for the operator to confirm or override. Until the operator responds, produce no
draft, write nothing to Apollo, send nothing, and take no external side effect of any kind.
The proposal is a proposal, not an action. If the operator overrides, use the outcome they
give.

## Step 4 - Branch on the confirmed outcome

Look up the confirmed outcome in `reference/outcome-taxonomy.md` and route by its branch.

**Stop-and-report branch.** For an outcome the taxonomy marks stop-and-report, output the
outcome label and the manual next step that the taxonomy lists for it, then stop. Produce no
draft of any kind and make no write to Apollo. Example:

> "Outcome: **fridge**
> Manual next step: park the deal in Apollo and set a reminder to revisit. No draft and no
> stage write from me on this one."

**Draft branch - hand off to `client-proposal-doc-builder`.** For an outcome the taxonomy
marks draft-and-Apollo-write (`proposal` and `needs_followup`), hand off to the
`client-proposal-doc-builder` skill and let it produce the draft. That is a separate skill the
operator must have installed; if it is not available, say so and stop the draft branch here.
Do not build the proposal or write the email here. This skill owns triage and routing; `client-proposal-doc-builder` owns
the proposal document, the follow-up email, the email-route selection, and the rule against
fabricating prior-campaign references or proof points. Reproduce none of that in this file.

Pass three things to `client-proposal-doc-builder`:

- **The full transcript** - the same text you read in Step 2, so the builder grounds the draft
  in what the prospect actually said.
- **The confirmed outcome** - `proposal` or `needs_followup`. This selects what the builder
  produces.
- **The company name** - the prospect's company, inferred from the transcript. If the
  transcript does not name it clearly, ask the operator before handing off.

The confirmed outcome decides what comes back:

- **`proposal`** - the builder runs its full workflow: it creates the proposal Google Doc and
  gives you its URL, then drafts the follow-up email as plain-text subject and body on its
  proposal-link route, so the email carries the Google Doc link.
- **`needs_followup`** - the builder skips the proposal document and drafts only the follow-up
  email as plain-text subject and body on its needs-followup route. No document, no link.

The builder drafts only - it does not send anything and does not return structured fields. It
hands back the doc URL (for `proposal`) and the drafted subject/body as text. This skill owns
the send (Step 5).

When the builder returns, present the draft to the operator for review: the proposal doc link
plus the email for `proposal`, the email alone for `needs_followup`.

After the operator has reviewed the draft, send the approved follow-up email (Step 5), then
update the Apollo deal stage (Step 6).

## Step 5 - Send the approved follow-up email

This step runs only on a confirmed `proposal` or `needs_followup` outcome, after the operator
has reviewed the draft from `client-proposal-doc-builder`. The other five outcomes never reach
it. The email goes out through the Gmail connector.

Before anything sends:

- **Find the recipient.** Use the prospect's email address from the discovery context: the
  transcript, the calendar event, or the contact the operator names. If you cannot determine a
  usable recipient, stop and say so. Do not send to a guessed or empty address.
- **Get explicit approval.** Show the operator the final email - recipient, subject, and body -
  and require an explicit "yes" to send. Do not treat "sure", "ok", or "yeah" as approval. If
  the operator edits the copy, send the edited version. Send nothing until they approve.

On approval, send the subject and body to the recipient through the Gmail connector, then:

- Confirm the send succeeded and report it.
- If the send fails, report the failure plainly and do not claim it went out.

No email is ever sent without a usable recipient and the operator's explicit approval.

## Step 6 - Update the Apollo deal stage

This step runs only on a confirmed `proposal` or `needs_followup` outcome, after the follow-up
email step (Step 5). The other five outcomes never reach it; they stop and report.

Read `apollo_stage_update.py` and follow its `EXECUTION_GUIDE`. Look up the target stage for
the confirmed outcome in `reference/outcome-taxonomy.md` (the outcome-to-Apollo-stage map); the
EXECUTION_GUIDE does not restate the map. The target stage is a logical label - the operator's
Apollo pipeline may name it differently or not have it - so the real column is confirmed with
the operator before any write. Then, through Claude-in-Chrome browser automation on
a logged-in Apollo:

- Search Apollo opportunities for the company name (the same name passed to
  `client-proposal-doc-builder`).
- Show the matched opportunity and its current stage, and require an explicit operator "yes"
  before any write.
- On zero or multiple matches, let the operator pick or supply the opportunity. The calendar or
  transcript name often differs from the Apollo account name (agency vs end-client, campaign
  alias); the operator resolves that here, in the session. There is no alias table.
- On confirmation, flip the stage to the target and verify the change took.

Never write on a best-guess match. No silent top-match write. If the operator declines or no
opportunity is confirmed, change nothing and say so.

## Completion summary

At the end of a run, output a short summary so the operator can verify it at a glance. The
summary always reports:

- **Outcome** - the confirmed outcome label.
- **Reasoning** - the one line that explained the outcome.

For a stop-and-report outcome, the summary adds the **manual next step** and states plainly
that no draft was produced and no Apollo write happened.

For a draft-and-Apollo-write outcome (the two outcomes the taxonomy marks as such), the
summary also reports:

- **Draft** - for `proposal`, confirmation that the proposal Google Doc was created (with its
  link) and the follow-up email was drafted. For `needs_followup`, confirmation that the
  follow-up email was drafted, with no proposal document.
- **Email sent** - confirmation that the approved email was sent through Gmail, or the failure
  if it did not send.
- **Apollo stage** - confirmation of the stage the deal was moved to, or that the write was
  skipped because the opportunity match was not confirmed.

This summary is the operator's single record of the run: the outcome, the proposal doc link (if
one was made), whether the email sent, and the Apollo stage set, or which of those was skipped
and why.

## Voice

Claude's own messages in this skill (the greeting, the outcome proposal, the branch output,
the completion summary) follow these voice rules:

- No AI-tell openers. Start with the substance, not a filler opener.
- No hedging qualifiers. State the read plainly.
- No AI-vocabulary buzzwords.
- No em-dashes. Use a hyphen or rewrite.
- Short. Direct. One idea per sentence.

## Reference

- `reference/outcome-taxonomy.md` - the seven outcomes, the classification criteria, the
  outcome-to-Apollo-stage map, and the draft-vs-report branching. Single source of truth for
  triage and Apollo routing. Read it when you classify and when you branch.
- `apollo_stage_update.py` - the browser EXECUTION_GUIDE for the Apollo deal-stage update
  (search, confirm, flip, verify). Read it in Step 6. The outcome-to-stage map it uses lives in
  `reference/outcome-taxonomy.md`, not in the .py. The `.py` file is data the skill reads at
  runtime - not a script to run, not a doc to edit.
