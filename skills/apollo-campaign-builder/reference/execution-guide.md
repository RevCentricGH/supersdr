# Apollo Campaign Builder - Execution Guide

Click-by-click detail for the browser steps in `SKILL.md`. Read this before starting Step 2.

## Step 2 - Sequence build loop

**Before starting:**
- Confirm the browser is open and logged in at app.apollo.io
- Navigate to `https://app.apollo.io/#/sequences`
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

## Step 4 - Verification checklist

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

## Visual campaign map

After verification, output a Mermaid diagram showing how the 4 workflows route SDR dispositions into sequences. Harnesses that render Mermaid show the user a single visual that maps the entire campaign logic; in a plain-text harness the code block still documents the routing.

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

## Troubleshooting

One issue at a time. Walk the user through the fix, then retry the step.

| Symptom | Likely cause and fix |
| --- | --- |
| A sequence will not save | A step is half-finished. Apollo blocks "Save changes" until every step has a type and timing set. Finish or delete the incomplete step, then click "Save changes" (top-right) again. |
| "Add to Sequence" picker shows no match | The sequence does not exist yet, or the typed name is off. Build all 7 sequences in Step 2 first, then build the workflows. In the picker, search the exact prefixed name ("{client} - ..."); the picker matches the saved sequence name. |
| Workflow stays in "Draft" after clicking Launch | A block is incomplete, so Apollo refuses to activate it. The usual culprits: the trigger has no Contact stage selected, or an action block (sequence, deal, list, or contact stage) has no value set. Open the workflow, fix the flagged block, then click "Launch workflow" again; the status flips from Draft to Active. |

## Voice Rules

Apply to all skill-authored output - greetings, confirmations, step reports, error messages.

- No AI-tell openers: "Great question", "Absolutely", "Certainly", "Of course"
- No hedging: "I think", "it seems", "potentially", "it's worth noting"
- No AI vocabulary: "delve", "leverage", "utilize", "robust", "seamless", "comprehensive"
- No em-dashes. Hyphen or rewrite.
- Short. Direct. One idea per sentence.
