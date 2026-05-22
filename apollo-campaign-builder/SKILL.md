---
name: apollo-campaign-builder
description: Set up a new client's full Apollo campaign — automatically create all 7 outreach sequences and 3 workflow plays in the Apollo UI using browser automation. Use when user says "set up Apollo for [client]", "build Apollo campaign for [client]", "run Apollo campaign builder", or provides a SPOT doc and asks to set up outreach sequences.
---

# Apollo Campaign Builder

> **STATUS: DRY-RUN VALIDATED 2026-05-20.** UI references in `sequence_builder.py` and `workflow_builder.py`'s `EXECUTION_GUIDE` constants were validated against the live Apollo UI via a manual dry run on 2026-05-20. Re-validate after any major Apollo UI release and bump the date in all three files when you do.

## Purpose

Browser-automation skill for onboarding a new client into Apollo. Creates all 7 outreach sequences and 3 workflow plays directly in the Apollo UI — no manual clicking.

Run this skill after the SPOT doc is complete. The lead list is built separately; this skill starts from the point where Apollo is open and the client name is confirmed.

## Files

- `sequence_builder.py` — step definitions for all 7 sequences + browser execution guide
- `workflow_builder.py` — definitions for all 3 workflow plays + browser execution guide

---

## What You Need Before Starting

- Client name confirmed — all sequences/workflows will be prefixed with it
- Apollo open and logged in at app.apollo.io in Chrome

---

## Getting started

When this skill is loaded, greet the user:

> "I'm the Apollo Campaign Builder. Tell me the client name and I'll set up all 7 outreach sequences and 3 workflow plays in your Apollo account."

Assume Apollo is open in Chrome and browser automation is enabled in Cowork. Try to navigate to `https://app.apollo.io/#/sequences` and start the workflow.

**Only if something fails**, walk the user through the fix one issue at a time:

- **Page redirects to login or doesn't load** → "Apollo isn't open or you're not logged in. Open Chrome, go to app.apollo.io, log in, then tell me you're ready."
- **Browser navigation fails entirely / Computer Use not available** → "Browser control isn't enabled in Cowork. Go to Settings → Computer Use and turn it on, then come back."

---

## Step 1 — Confirm Client Name

Ask the user to confirm the client name. This prefixes every sequence and workflow name (e.g., "Acme Corp - Call Only"). If a SPOT doc is provided, pull the client name from Tab 1 or Tab 9 — otherwise ask directly.

```
Client name confirmed: {ClientName}
All sequences and workflows will be prefixed: "{ClientName} - ..."
```

---

## Step 2 — Create All 7 Sequences (Browser Automation)

Read `sequence_builder.py` — it contains the full step definitions for all 7 sequences and the execution guide in `EXECUTION_GUIDE`.

**Before starting:**
- Confirm Chrome is open and logged in at app.apollo.io
- Use `mcp__Claude_in_Chrome__navigate` to go to `https://app.apollo.io/#/sequences`
- Verify the page loads (not redirected to login)

**For each sequence 1–7 in `sequence_builder.SEQUENCES`:**

1. Navigate to `https://app.apollo.io/#/sequences`
2. Click "New Sequence" / "Create Sequence"
3. Enter the name: `{client} - {sequence["name"]}` (e.g. "Acme Corp - Call Only")
4. Confirm creation — wait for the steps editor to load
5. For each step in `sequence["steps"]`:
   - Click "Add a step"
   - Select the step type: Phone Call / Manual Email / Automatic Email / Action Item
   - Set the timing (`delay` + `unit`) — "immediately" means 0 / leave blank
   - Save the step and wait for it to appear in the list
6. Verify step count matches `len(sequence["steps"])` — if wrong, stop and flag
7. Activate the sequence
8. Note the sequence ID from the URL for Step 3

After each sequence confirm:
```
✓ Sequence {n}: {name} — {step_count} steps, active
```

After all 7:
```
All 7 sequences created:
  1. {client} - Call Only          (10 steps)
  2. {client} - Activated Lead     (7 steps)
  3. {client} - Nurture            (7 steps)
  4. {client} - Cold Follow-Up     (14 steps)
  5. {client} - Pending Meeting    (2 steps)
  6. {client} - Reschedule         (10 steps)
  7. {client} - Referred To        (10 steps)
```

If a step modal behaves unexpectedly — screenshot and report before retrying. Do not skip steps.

---

## Step 3 — Create the 3 Workflow Plays (Browser Automation)

Read `workflow_builder.py` — it contains the full workflow definitions and execution guide in `EXECUTION_GUIDE`.

**Navigate** to `https://app.apollo.io/#/workflows`

**For each workflow 1–3 in `workflow_builder.WORKFLOWS`:**

1. Click "New Workflow" / "Create Workflow"
2. Enter the name: `{client} - Disposition: {disposition}`
3. Set the trigger: disposition change → the value from `workflow["trigger"]["disposition"]`
4. Add each action in order per `workflow["actions"]`:
   - **Add to Sequence**: search and select the exact client sequence by name
   - **Create Deal**: set the deal stage from `action["deal_stage"]`
   - **Associate Contact to Deal**: link contact to the deal above
   - **Add to List**: enter the list name from `action["list_name"]`
5. **Before saving**: if the action is "Add to Sequence", confirm the selected sequence
   name contains the client name — wrong sequence is the #1 setup error
6. Save and activate

After all 3:
```
All 3 workflows created:
  1. {client} - Disposition: Activated Lead  (active)
  2. {client} - Disposition: Nurture         (active)
  3. {client} - Disposition: Meeting Booked  (active)
```

---

## Step 4 — Verification Checklist

Confirm each item and report to the user:

```
SEQUENCES
[ ] Call Only          — 10 steps, active, prefixed with client name
[ ] Activated Lead     — 7 steps, active
[ ] Nurture            — 7 steps, active
[ ] Cold Follow-Up     — 14 steps, active
[ ] Pending Meeting    — 2 steps, active
[ ] Reschedule         — 10 steps, active
[ ] Referred To        — 10 steps, active

WORKFLOWS
[ ] Disposition: Activated Lead  — active, sequence name shows [client]
[ ] Disposition: Nurture         — active, sequence name shows [client]
[ ] Disposition: Meeting Booked  — active, sequence + list names show [client]
```

## Step 5 — Visual campaign map

After verification, output a Mermaid diagram showing how the 3 workflows route SDR dispositions into sequences. Cowork renders this natively — gives the user a single visual that maps the entire campaign logic.

````
```mermaid
flowchart TD
    SDR[SDR sets contact disposition]
    SDR --> AL{Activated Lead}
    SDR --> NT{Nurture}
    SDR --> MB{Meeting Booked}

    AL --> AL_SEQ[Sequence:<br/>{client} - Activated Lead<br/>7 steps]
    AL --> AL_DEAL[Create Deal<br/>stage: Activated Lead]
    AL --> AL_LINK[Associate Contact<br/>to Deal]

    NT --> NT_SEQ[Sequence:<br/>{client} - Nurture<br/>7 steps]

    MB --> MB_LIST[Add to List:<br/>{client} - Meetings Booked]
    MB --> MB_SEQ[Sequence:<br/>{client} - Pending Meeting<br/>2 steps]

    OTHER[Other entry points] -.-> CO[{client} - Call Only<br/>10 steps]
    OTHER -.-> CFU[{client} - Cold Follow-Up<br/>14 steps]
    OTHER -.-> RS[{client} - Reschedule<br/>10 steps]
    OTHER -.-> RF[{client} - Referred To<br/>10 steps]

    style AL fill:#fff3e0
    style NT fill:#e8f5e9
    style MB fill:#e3f2fd
```
````

Substitute `{client}` with the actual client name. The dotted lines from "Other entry points" represent the 4 sequences that aren't workflow-triggered — SDRs add contacts to those manually.

When all boxes are checked and the visual map is rendered, the client is fully set up in Apollo and ready to run.
