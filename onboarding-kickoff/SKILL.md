---
name: onboarding-kickoff
description: Kick off onboarding for a client who just paid, inside Cowork with the operator present. Trigger when the operator says a client signed or paid and wants to start onboarding, or says things like "run onboarding-kickoff", "client just paid, start onboarding", "kick off onboarding for [client]", "send the welcome email", or pastes the closing-call transcript and asks to start onboarding. The skill takes the client context (name and details, or the closing-call transcript) and the onboarding-form link, drafts the welcome and onboarding-form email, waits for the operator to review and approve it, then sends it through the Gmail connector. It then moves the client's Apollo opportunity to the onboarding stage with a search-and-confirm lookup. It halts with a clear message if there is no usable recipient. It ends by handing off to client-spot to build the SPOT and start fulfillment. It does not create the SPOT itself.
---

# Onboarding Kickoff

A Cowork skill the operator runs once a client has paid. It drafts the welcome and
onboarding-form email, lets the operator review and approve it, sends it through the Gmail
connector, moves the client's Apollo opportunity to the onboarding stage, and ends by handing
off to `client-spot`. It runs with the operator in the session; nothing goes out and no stage
moves without their explicit approval.

This skill is the clean start of fulfillment. It sends the first email, advances the deal, and
points the operator at the next skill. It does not build the SPOT - that keeps the acquisition
and fulfillment work in their own lanes.

**Runtime: Claude Cowork**

## Getting started

When the skill loads, greet the operator:

> "I kick off onboarding for a client who just paid. I'll draft the welcome and onboarding-form
> email, let you approve it, and send it through Gmail. Then I'll hand you off to client-spot to
> build the SPOT.
>
> Tell me the client (name and a line of context, or paste the closing-call transcript) and the
> onboarding-form link. If the form link is the same every time, give it to me once and I'll use
> it. After the email goes out I'll move the deal to the onboarding stage in Apollo, with your
> confirmation."

Wait for the client context and the form link before doing anything else.

## Step 1 - Intake the client and the form link

Collect two things:

- **The client context.** Either the client name plus a line of context, or the closing-call
  transcript. If the operator pastes a transcript, read it in full and pull the client name, the
  contact's name, and the contact's email if it is in there. Do not classify or guess from a
  preview - read the whole thing.
- **The onboarding-form link.** The operator supplies it, or it is a fixed link they gave you
  once in this session. If you have no form link, ask for it before drafting; the email is built
  around it.

If the operator gives neither a transcript nor a client name, ask for the client before going on.

## Step 2 - Draft the welcome and onboarding-form email

Draft a short welcome email that congratulates the client, says what happens next, and points
them at the onboarding form to fill in. Keep it warm and plain. The onboarding-form link is the
one action the email asks for - make it clear and unmissable.

Draft as plain-text subject and body. Do not invent details the operator did not give: no made-up
start dates, deliverables, pricing, or names. If a useful detail is missing, leave it out or ask
the operator rather than filling it in. The signature uses the operator's own name and company,
not a hardcoded person - ask if you do not have it.

## Step 3 - Confirm the recipient

Find the recipient before anything sends:

- Use the contact's email from the client context: the transcript, the contact the operator
  names, or an address the operator supplies.
- If you cannot determine a usable recipient, **stop and say so.** Do not send to a guessed or
  empty address, and do not proceed to the send step. Ask the operator for the recipient and
  wait.

A run with no usable recipient halts here. It does not send and does not move the Apollo stage.

## Step 4 - Approve and send through Gmail

Show the operator the final email - recipient, subject, and body - and require an explicit "yes"
to send. Do not treat "sure", "ok", or "yeah" as approval. If the operator edits the copy, send
the edited version. Send nothing until they approve.

On approval, send the subject and body to the recipient through the Gmail connector, then:

- Confirm the send succeeded and report it.
- If the send fails, report the failure plainly and do not claim it went out.

No email is ever sent without a usable recipient and the operator's explicit approval.

## Step 5 - Move the Apollo opportunity to the onboarding stage

This step runs after the email step (Step 4), whether the email sent or its send was reported as
failed. It does not run on a no-recipient halt - that run already stopped at Step 3.

Read `apollo_stage_update.py` and follow its `EXECUTION_GUIDE`. The target is the onboarding
stage. That is a logical label - the operator's Apollo pipeline may name it differently, track
onboarding in a separate pipeline, or not have the column - so the real column is confirmed with
the operator before any write. Then, through the Claude in Chrome browser extension on a
logged-in Apollo:

- Search Apollo deals for the company name (the same client carried through this skill).
- Show the matched deal and its current stage, and require an explicit operator "yes" before any
  write.
- On zero or multiple matches, let the operator pick or supply the deal. The transcript name
  often differs from the Apollo account name (agency vs end-client, campaign alias); the operator
  resolves that here, in the session. There is no alias table.
- On confirmation, move the deal to the onboarding column and verify the move took.

Never write on a best-guess match. No silent top-match write. If the operator declines or no deal
is confirmed, change nothing and say so.

## Step 6 - Hand off to client-spot

After the stage step, end with the handoff. Do not build the SPOT here and do not chain into the
other skill automatically - tell the operator to run it:

> "Welcome email sent and the deal is in the onboarding stage. Next, run `client-spot` to build
> this client's SPOT and start fulfillment. Paste the onboarding-form response and any call notes
> into that skill when you have them."

This skill stops at the handoff. Creating the SPOT is `client-spot`'s job.

## Completion summary

At the end of a run, output a short summary so the operator can verify it at a glance:

- **Client** - the client name as confirmed.
- **Email sent** - confirmation that the approved welcome email was sent through Gmail (with the
  recipient), or the failure if it did not send.
- **Stage set** - confirmation that the deal was moved to the onboarding stage (with the column
  name), or that the move was skipped because the deal match was not confirmed or no column fit.
- **Handoff** - that the next step is to run `client-spot`.

If the run halted because there was no usable recipient, say that plainly: no email was sent, no
stage was moved, and the operator needs to supply a recipient to continue.

## Voice

Claude's own messages in this skill (the greeting, the draft, the approval ask, the handoff, the
completion summary) follow these voice rules:

- No AI-tell openers. Start with the substance, not a filler opener.
- No hedging qualifiers. State things plainly.
- No AI-vocabulary buzzwords.
- No em-dashes. Use a hyphen or rewrite.
- Short. Direct. One idea per sentence.

## Reference

- `apollo_stage_update.py` - the browser EXECUTION_GUIDE for the Apollo onboarding-stage move
  (search, confirm, move, verify). Read it in Step 5. The skill bundles its own copy so it ships
  as a standalone ZIP. The `.py` file is data the skill reads at runtime - not a script to run,
  not a doc to edit.
