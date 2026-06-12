---
name: apollo-campaign-builder
description: Set up a new client's full Apollo campaign - automatically create all 7 outreach sequences and 4 workflow plays in the Apollo UI using browser automation. Use when user says "set up Apollo for [client]", "build Apollo campaign for [client]", "run Apollo campaign builder", or provides a SPOT doc and asks to set up outreach sequences.
capabilities: [drive a web browser]
---

# Apollo Campaign Builder

**Runtime:** any agentic harness with browser automation

## Purpose

Browser-automation skill for onboarding a new client into Apollo. Creates all 7 outreach sequences and 4 workflow plays directly in the Apollo UI - no manual clicking.

Run this skill after the SPOT doc is complete. The lead list is built separately by `list-builder`; this skill starts from Apollo open in a browser and confirms the client name in Step 1.

## Files

- `sequence_builder.py` - step definitions for all 7 sequences + browser execution guide
- `workflow_builder.py` - definitions for all 4 workflow plays + browser execution guide
- `reference/execution-guide.md` - the click-by-click browser loop, verification checklist, campaign map, troubleshooting, voice rules

Both `.py` files are data the skill reads at runtime - not scripts to run, not docs to edit.

---

## Required capability: drive a web browser

This skill requires browser automation - the ability to navigate, click, and type inside a live browser session. Apollo has no API for sequences or workflows; the UI is the only way to build them.

If the host cannot navigate and click inside a live browser, stop immediately and tell the user:

> "apollo-campaign-builder requires browser automation; there is no text-only fallback. Enable browser automation before running this skill."

Do not offer a manual checklist or degrade to text instructions. Missing capability = hard stop.

---

## Prerequisites

- Client name confirmed - all sequences/workflows will be prefixed with it
- Apollo open and logged in at app.apollo.io in the browser
- `apollo-account-setup` run once on this Apollo account - the workflow plays reference contact stages it creates, and they will not save without them
- Deal pipeline has an "Activated Lead" stage - Workflow 2's Create Deal action targets it. This is a custom pipeline stage, not an Apollo default and not created by `apollo-account-setup`; add it in Settings → Deals → Pipeline before building workflows, or Workflow 2 stays stuck in Draft

---

## Getting started

When this skill is loaded, greet the user:

> "I'm the Apollo Campaign Builder. Tell me the client name and I'll set up all 7 outreach sequences and 4 workflow plays in your Apollo account."

Assume Apollo is open and logged in and browser automation is available. Navigate to `https://app.apollo.io/#/sequences` and start the workflow. If the page redirects to login or doesn't load, tell the user: "Apollo isn't open or you're not logged in. Open your browser, go to app.apollo.io, log in, then tell me you're ready."

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

Build each of the 7 sequences in `sequence_builder.SEQUENCES` in the Apollo UI: create the sequence with the client-prefixed name, add every step with its type and timing, verify the step count, and activate it.

> **Before Step 2:** Read `reference/execution-guide.md` now - the click-by-click browser loop is there. Do not begin Step 2 without it.

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

## Step 4 - Verify and map

Run the verification checklist and output the visual campaign map - both are in `reference/execution-guide.md`. When every box is checked and the map is rendered, the client is fully set up in Apollo and ready to run.

For any error along the way, use the Troubleshooting table in `reference/execution-guide.md` - one issue at a time. Apply the Voice Rules there to all output.
