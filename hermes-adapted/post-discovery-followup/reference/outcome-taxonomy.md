# Outcome taxonomy

Single source of truth for post-discovery triage and Apollo routing. The orchestrator
(`SKILL.md`) and every later slice read this file. Outcome definitions, classification
criteria, the outcome-to-Apollo-stage map, and the draft-vs-report branching assignment
live here and nowhere else. If any of those facts need to change, change them here.

Interface:

- Transcript in, one proposed outcome out (with one line of reasoning).
- Confirmed outcome in, target Apollo stage and branch out.

## The seven outcomes

Every discovery call resolves to exactly one of these values:

`proposal`, `needs_followup`, `closed_won`, `closed_lost`, `fridge`, `disqualified`,
`stay_in_proposal`.

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

## Branching: draft-and-Apollo-write vs stop-and-report

Two outcomes branch to draft-and-Apollo-write. The skill produces a draft (proposal document
or follow-up email) through `client-proposal-doc-builder` and, after operator approval,
updates the Apollo stage:

- `proposal` (full proposal document)
- `needs_followup` (follow-up email only, no proposal document)

The other five outcomes branch to stop-and-report. The skill reports the outcome label and
the manual next step, then stops. No draft, no Apollo write:

- `closed_won` (manual next step: confirm paperwork, set the stage to Closed Won by hand)
- `closed_lost` (manual next step: set the stage to Closed Lost by hand)
- `fridge` (manual next step: park the deal and set a reminder to revisit)
- `disqualified` (manual next step: set the stage to Disqualified by hand)
- `stay_in_proposal` (manual next step: leave the stage unchanged; note the call for the next touch)

`stay_in_proposal` is a stop-and-report outcome. Even though the deal sits in the proposal
stage, this call produces no new draft and triggers no Apollo write. The five stop-and-report
outcomes report only; their stage moves stay manual, which keeps this skill in its Phase 1
lane and out of Phase 3 side effects.
