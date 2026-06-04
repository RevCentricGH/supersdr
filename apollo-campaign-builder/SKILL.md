---
name: apollo-campaign-builder
description: Set up a new client's full Apollo campaign - automatically create all 7 outreach sequences and 4 workflow plays in the Apollo UI using browser automation. Use when user says "set up Apollo for [client]", "build Apollo campaign for [client]", "run Apollo campaign builder", or provides a SPOT doc and asks to set up outreach sequences.
---

# Apollo Campaign Builder

**Runtime:** Claude Cowork

## Purpose

Browser-automation skill for onboarding a new client into Apollo. Creates all 7 outreach sequences and 4 workflow plays directly in the Apollo UI - no manual clicking.

Run this skill after the SPOT doc is complete. The lead list is built separately by `list-builder`; this skill starts from Apollo open in Chrome and confirms the client name in Step 1.

## Files

- `sequence_builder.py` - step definitions for all 7 sequences + browser execution guide
- `workflow_builder.py` - definitions for all 4 workflow plays + browser execution guide

Both `.py` files are data the skill reads at runtime - not scripts to run, not docs to edit.

---

## Prerequisites

- Client name confirmed - all sequences/workflows will be prefixed with it
- Apollo open and logged in at app.apollo.io in Chrome
- `apollo-account-setup` run once on this Apollo account - the workflow plays reference contact stages it creates, and they will not save without them
- Deal pipeline has an "Activated Lead" stage - Workflow 2's Create Deal action targets it. This is a custom pipeline stage, not an Apollo default and not created by `apollo-account-setup`; add it in Settings → Deals → Pipeline before building workflows, or Workflow 2 stays stuck in Draft

---

## Getting started

When this skill is loaded, greet the user:

> "I'm the Apollo Campaign Builder. Tell me the client name and I'll set up all 7 outreach sequences and 4 workflow plays in your Apollo account."

Assume Apollo is open in Chrome and browser automation is enabled in Cowork. Try to navigate to `https://app.apollo.io/#/sequences` and start the workflow.

**Only if something fails**, walk the user through the fix one issue at a time:

- **Page redirects to login or doesn't load** → "Apollo isn't open or you're not logged in. Open Chrome, go to app.apollo.io, log in, then tell me you're ready."
- **Browser navigation fails entirely / browser automation not available** → "Browser automation (Claude in Chrome) isn't enabled. Go to Settings → Computer Use, turn on browser control, then come back."

---

## Step 1 - Confirm Client Name

Ask the user to confirm the client name. This prefixes every sequence and workflow name (e.g., "Acme Corp - Call Only"). If a SPOT doc is provided, pull the client name from Tab 1 or Tab 9 - otherwise ask directly.

```
Client name confirmed: {ClientName}
All sequences and workflows will be prefixed: "{ClientName} - ..."
```

---

## Step 2 - Create All 7 Sequences (Browser Automation)

Read `sequence_builder.py` - it contains the full step definitions for all 7 sequences and the execution guide in `EXECUTION_GUIDE`.

**Before starting:**
- Confirm Chrome is open and logged in at app.apollo.io
- Use `mcp__Claude_in_Chrome__navigate` to go to `https://app.apollo.io/#/sequences`
- Verify the page loads (not redirected to login)

**For each sequence 1–7 in `sequence_builder.SEQUENCES`:**

1. Navigate to `https://app.apollo.io/#/sequences`
2. Click "New Sequence" / "Create Sequence"
3. Enter the name: `{client} - {sequence["name"]}` (e.g. "Acme Corp - Call Only")
4. Confirm creation - wait for the steps editor to load
5. For each step in `sequence["steps"]`:
   - Click "Add a step"
   - Select the step type: Phone Call / Manual Email / Automatic Email / Action Item
   - Set the timing (`delay` + `unit`) - "immediately" means 0 / leave blank
   - Save the step and wait for it to appear in the list
6. Verify step count matches `len(sequence["steps"])` - if wrong, stop and flag
7. Activate the sequence
8. Note the sequence ID from the URL for Step 3

After each sequence confirm:
```
✓ Sequence {n}: {name} - {step_count} steps, active
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

If a step modal behaves unexpectedly - screenshot and report before retrying. Do not skip steps.

---

## Step 3 - Create the 4 Workflow Plays (Browser Automation)

Read `workflow_builder.py` - it contains the full workflow definitions and execution guide in `EXECUTION_GUIDE`.

**Navigate** to `https://app.apollo.io/#/workflows`

**The #1 setup error is pointing a workflow at another client's sequence.** Before saving any workflow, verify every selected sequence name contains this client's name.

**For each workflow 1–4 in `workflow_builder.WORKFLOWS`:**

1. Click "New Workflow" / "Create Workflow"
2. Enter the name: `{client} - Disposition: {disposition}`
3. Set the trigger: disposition change → the value from `workflow["trigger"]["disposition"]`
4. Add each action in order per `workflow["actions"]`:
   - **Add to Sequence**: search and select the exact client sequence by name
   - **Create Deal**: set the deal stage from `action["deal_stage"]`
   - **Associate Contact to Deal**: link contact to the deal above
   - **Add to List**: enter the list name from `action["list_name"]`
   - **Update Contact Stage**: set the stage from `action["stage"]`
5. **Before saving**: if the action is "Add to Sequence", confirm the selected sequence
   name contains the client name - wrong sequence is the #1 setup error
6. Save and activate

**Trigger vocabulary:** Apollo's trigger event is "Contact updated", not "Disposition changed". The "Contact stage" field in the trigger holds the stage value the workflow definitions set. This naming is maintained by hand; the guard test only checks that every action type is documented above.

After all 4:
```
All 4 workflows created:
  1. {client} - Disposition: Meeting Scheduled  (active)
  2. {client} - Disposition: Activated Lead     (active)
  3. {client} - Disposition: Connect Incomplete (active)
  4. {client} - Disposition: Nurture            (active)
```

---

## Step 4 - Verification Checklist

Confirm each item and report to the user:

```
SEQUENCES
[ ] Call Only          - 10 steps, active, prefixed with client name
[ ] Activated Lead     - 7 steps, active
[ ] Nurture            - 7 steps, active
[ ] Cold Follow-Up     - 14 steps, active
[ ] Pending Meeting    - 2 steps, active
[ ] Reschedule         - 10 steps, active
[ ] Referred To        - 10 steps, active

WORKFLOWS
[ ] Disposition: Meeting Scheduled  - active, sequence + list names show [client]
[ ] Disposition: Activated Lead     - active, sequence name shows [client]
[ ] Disposition: Connect Incomplete - active, sequence name shows [client]
[ ] Disposition: Nurture            - active, sequence name shows [client]
```

## Step 5 - Visual campaign map

After verification, output a Mermaid diagram showing how the 4 workflows route SDR dispositions into sequences. Cowork renders this natively - gives the user a single visual that maps the entire campaign logic.

````
```mermaid
flowchart TD
    SDR[SDR sets contact disposition]
    SDR --> MS{Meeting Scheduled}
    SDR --> AL{Activated Lead}
    SDR --> CI{Connect Incomplete}
    SDR --> NT{Nurture}

    MS --> MS_LIST[Add to List:<br/>{client} - Meetings Booked]
    MS --> MS_SEQ[Sequence:<br/>{client} - Pending Meeting<br/>2 steps]
    MS --> MS_STAGE[Stage: Meeting Pending]

    AL --> AL_SEQ[Sequence:<br/>{client} - Activated Lead<br/>7 steps]
    AL --> AL_DEAL[Create Deal<br/>stage: Activated Lead]
    AL --> AL_LINK[Associate Contact to Deal]
    AL --> AL_STAGE[Stage: Activated Lead]

    CI --> CI_SEQ[Sequence:<br/>{client} - Cold Follow-Up<br/>14 steps]
    CI --> CI_STAGE[Stage: Approaching]

    NT --> NT_SEQ[Sequence:<br/>{client} - Nurture<br/>7 steps]
    NT --> NT_STAGE[Stage: Nurture]

    OTHER[Manual entry points] -.-> CO[{client} - Call Only<br/>10 steps]
    OTHER -.-> RS[{client} - Reschedule<br/>10 steps]
    OTHER -.-> RF[{client} - Referred To<br/>10 steps]

    style MS fill:#e3f2fd
    style AL fill:#fff3e0
    style CI fill:#fce4ec
    style NT fill:#e8f5e9
```
````

Substitute `{client}` with the actual client name. The dotted lines from "Other entry points" represent the 4 sequences that aren't workflow-triggered - SDRs add contacts to those manually.

When all boxes are checked and the visual map is rendered, the client is fully set up in Apollo and ready to run.

---

## Troubleshooting

One issue at a time. Walk the user through the fix, then retry the step.

| Symptom | Likely cause and fix |
| --- | --- |
| A sequence will not save | A step is half-finished. Apollo blocks "Save changes" until every step has a type and timing set. Finish or delete the incomplete step, then click "Save changes" (top-right) again. |
| "Add to Sequence" picker shows no match | The sequence does not exist yet, or the typed name is off. Build all 7 sequences in Step 2 first, then build the workflows. In the picker, search the exact prefixed name ("{client} - ..."); the picker matches the saved sequence name. |
| Workflow stays in "Draft" after clicking Launch | A block is incomplete, so Apollo refuses to activate it. The usual culprits: the trigger has no Contact stage selected, or an action block (sequence, deal, list, or contact stage) has no value set. Open the workflow, fix the flagged block, then click "Launch workflow" again; the status flips from Draft to Active. |

---

## Voice Rules

Apply to all Claude-authored output - greetings, confirmations, step reports, error messages.

- No AI-tell openers: "Great question", "Absolutely", "Certainly", "Of course"
- No hedging: "I think", "it seems", "potentially", "it's worth noting"
- No AI vocabulary: "delve", "leverage", "utilize", "robust", "seamless", "comprehensive"
- No em-dashes. Hyphen or rewrite.
- Short. Direct. One idea per sentence.
