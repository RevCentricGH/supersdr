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

**Draft-and-Apollo-write branch.** For an outcome the taxonomy marks draft-and-Apollo-write,
hand the transcript, the confirmed outcome, and the company name to `client-proposal-doc-builder`
and let it produce the draft (a full proposal document or a follow-up email, per the outcome).
On its return, present the draft for approval, send the approved email through the Gmail
connector, and update the deal stage in Apollo through browser automation after the operator
confirms the matched opportunity.

The handoff, the Gmail send, and the Apollo stage update are built in the later slices of this
skill (issues #16 through #19). In this walking skeleton, route a draft outcome to the
proposal-builder handoff and stop there. Do not duplicate any proposal or email logic in this
file.

## Completion summary

<!-- COMPLETION SUMMARY SHELL: what a successful run outputs at the end. -->

At the end of a run, output a short summary so the operator can verify it at a glance. The
summary always reports:

- **Outcome** - the confirmed outcome label.
- **Reasoning** - the one line that explained the outcome.

For a stop-and-report outcome, the summary adds the **manual next step** and states plainly
that no draft was produced and no Apollo write happened.

For a draft-and-Apollo-write outcome (the two outcomes the taxonomy marks as such), the
summary also reports:

- **Draft** - confirmation that the proposal document or follow-up email was drafted, with the
  Google Doc link for a proposal.
- **Email sent** - confirmation that the approved email was sent through Gmail, or the failure
  if it did not send.
- **Apollo stage** - confirmation of the stage the deal was moved to, or that the write was
  skipped because the opportunity match was not confirmed.

The send and Apollo lines of the summary are filled in by the later slices; this skeleton
ships the shell and the outcome and reasoning lines.

## Voice

Claude's own messages in this skill (the greeting, the outcome proposal, the branch output,
the completion summary) follow the repo voice rules in `CLAUDE.md`:

- No AI-tell openers. Start with the substance, not a filler opener.
- No hedging qualifiers. State the read plainly.
- No AI-vocabulary buzzwords.
- No em-dashes. Use a hyphen or rewrite.
- Short. Direct. One idea per sentence.

## Reference

- `reference/outcome-taxonomy.md` - the seven outcomes, the classification criteria, the
  outcome-to-Apollo-stage map, and the draft-vs-report branching. Single source of truth for
  triage and Apollo routing. Read it when you classify and when you branch.
