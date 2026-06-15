# Outcome taxonomy

Single source of truth for post-discovery triage and Apollo routing. The orchestrator
(`SKILL.md`) and every later slice read this file. Outcome definitions, the call-type
definitions, classification criteria, the outcome-to-Apollo-stage map, and the call-type
branching assignment live here and nowhere else. If any of those facts need to change, change
them here.

Interface:

- Transcript in, one proposed call type and one proposed outcome out (each with one line of
  reasoning).
- Confirmed call type plus confirmed outcome in, target Apollo stage and branch out.

## The seven outcomes

Every call resolves to exactly one of these values:

`proposal`, `needs_followup`, `closed_won`, `closed_lost`, `fridge`, `disqualified`,
`stay_in_proposal`.

## Call type: discovery vs closing

Every call is one of two types. Triage infers the call type from the full transcript and
proposes it alongside the outcome; the operator confirms or overrides the call type before any
branch runs. The call type decides how the five closing outcomes are handled (see Branching).

### discovery

The first real working call. The rep is qualifying the prospect and earning the right to send
a proposal. Signals: introductions, problem discovery, "what does your outbound look like
today," qualifying on need, budget, and authority, and a forward step that is a proposal or a
follow-up. No proposal is under review on this call.

### closing

A later call on a deal that already has a proposal in play. The rep and the prospect are
deciding the deal. Signals: a proposal or pricing already on the table, "did you get a chance
to review it," final objections, a yes-or-no decision, contract or paperwork talk, or an
explicit close. The deal is being resolved, not opened.

When the signals are mixed, prefer the more conservative read and let the operator override. A
call with no proposal in play is a discovery call.

## Classification criteria

Read the full transcript, then match it against these criteria in order. Pick the single
outcome that fits best. When two look close, prefer the more conservative read (a call that
might be `needs_followup` is not a `proposal`) and let the operator override.

### proposal

The prospect is qualified and the call earned the right to send a proposal. Signals: a real
need tied to outbound, budget or willingness to invest discussed, the right person in the
room or a clear path to them, and an explicit or implied ask for pricing, scope, or a written
proposal. The committed next step is a proposal document.

### needs_followup

The prospect is interested but a gap blocks a proposal. Signals: a missing piece of
information, a stakeholder who has to weigh in, a request for materials short of a full
proposal, or a "circle back next week" with intent intact. The next step is a follow-up
email, not a proposal document.

### closed_won

The prospect committed on the call. Signals: a verbal yes, agreement on terms, a request to
send paperwork, or "let's start." The deal is won.

### closed_lost

The prospect declined. Signals: an explicit no, a decision to go with a competitor or stay
in-house, or a hard stop on the engagement. The deal is lost after having been a real
opportunity.

### fridge

Genuine fit, wrong timing. Signals: a budget freeze, a reorg, a "not this quarter, ask me in
N months," or a priority that outranks this for now. The deal is parked, not dead, and gets
revisited later.

### disqualified

Not a fit. Signals: outside the ICP, no real need, wrong company size, no authority and no
path to it, or a budget that rules out the engagement. Different from `closed_lost`: this
opportunity never qualified in the first place.

### stay_in_proposal

The deal is already in the proposal stage and the call surfaced nothing that moves it forward
or kills it. Signals: a status check, a minor clarification, a "still reviewing internally."
It stays in proposal; no new document is warranted from this call.

A closing call naturally resolves to one of the five closing outcomes (`closed_won`,
`closed_lost`, `fridge`, `disqualified`, `stay_in_proposal`). If a call you read as closing
lands on `proposal` or `needs_followup`, treat that as a signal to re-check the call type with
the operator.

## Outcome-to-Apollo-stage map

Each outcome maps to one target Apollo opportunity stage. Stage labels below are the logical
stages; the operator maps them to the exact stage names in their own Apollo pipeline (the
skill is built for any operator's account, so nothing is hardcoded to one pipeline).

| Outcome | Target Apollo stage |
|---|---|
| `proposal` | Proposal Sent |
| `needs_followup` | Follow-up |
| `closed_won` | Closed Won |
| `closed_lost` | Closed Lost |
| `fridge` | Nurture / Fridge |
| `disqualified` | Disqualified |
| `stay_in_proposal` | Proposal Sent (unchanged) |

### Closing-call outcomes

On a closing call the five closing outcomes are actionable: each resolves the deal to its
target Apollo stage from the map above.

| Closing outcome | Target Apollo stage |
|---|---|
| `closed_won` | Closed Won |
| `closed_lost` | Closed Lost |
| `disqualified` | Disqualified |
| `fridge` | Nurture / Fridge |
| `stay_in_proposal` | Proposal Sent (unchanged) |

## Branching by call type

The call type decides the branch for the five closing outcomes. The two draft outcomes
(`proposal`, `needs_followup`) branch to draft-and-Apollo-write on either call type.

### draft-and-Apollo-write (`proposal`, `needs_followup`)

The skill produces a draft (proposal document or follow-up email) through
`client-proposal-doc-builder` and, after operator approval, updates the Apollo stage:

- `proposal` (full proposal document)
- `needs_followup` (follow-up email only, no proposal document)

This branch is the same on a discovery call or a closing call. On a closing call these two
outcomes are uncommon (a proposal is already in play), so when they come up there, re-check the
call type with the operator first.

### Discovery call: the five closing outcomes stop and report

On a discovery call the five closing outcomes stop and report. The skill reports the outcome
label and the manual next step, then stops. No draft, no Apollo write:

- `closed_won` (manual next step: confirm paperwork, set the stage to Closed Won by hand)
- `closed_lost` (manual next step: set the stage to Closed Lost by hand)
- `fridge` (manual next step: park the deal and set a reminder to revisit)
- `disqualified` (manual next step: set the stage to Disqualified by hand)
- `stay_in_proposal` (manual next step: leave the stage unchanged; note the call for the next touch)

### Closing call: the five closing outcomes route to post-closing handling

On a closing call the deal is being resolved, so these five outcomes are actionable rather than
report-only. Each routes to post-closing handling: the skill states the resolved outcome and
its target Apollo stage from the map above, and the deal moves to that stage on the confirmed
opportunity. This is the action track, not the report-only track the discovery path uses for
these outcomes.

- `closed_won` -> Closed Won
- `closed_lost` -> Closed Lost
- `disqualified` -> Disqualified
- `fridge` -> Nurture / Fridge
- `stay_in_proposal` -> stays in Proposal Sent; follow up manually

This file defines the call-type branch and the closing-stage targets. Moving the deal to the
target stage reuses the same Apollo stage-update flow the discovery path uses; confirm the
opportunity before any stage change.
