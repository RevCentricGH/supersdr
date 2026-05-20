---
name: rc-apollo-campaign-builder
description: Set up a new client's full Apollo campaign — build the initial lead list from SPOT ICP criteria, then automatically create all 7 outreach sequences and 3 workflow plays in the Apollo UI using browser automation. Use when user says "set up Apollo for [client]", "build Apollo campaign for [client]", "run Apollo campaign builder", "build the list for [client]", or provides a SPOT doc and asks to set up outreach sequences.
---

# Apollo Campaign Builder

## Purpose

Two-phase skill for onboarding a new client into Apollo:

1. **Automated** — search Apollo's API by ICP criteria from the SPOT → export contacts as CSV
2. **Automated** — use browser automation (Claude in Chrome MCP) to create all 7 sequences and 3 workflow plays directly in the Apollo UI — no manual clicking

Run this skill after the SPOT doc is complete. Tab 9 (Apollo Campaign Setup) is the primary input.

## Files

- `sequence_builder.py` — step definitions for all 7 RC sequences + browser execution guide
- `workflow_builder.py` — definitions for all 3 workflow plays + browser execution guide

---

## What You Need Before Starting

- SPOT doc (URL, Google Doc link, or pasted content)
- Apollo API key (Settings → Integrations → API) — for Phase 1 list build only
- Apollo open and logged in at app.apollo.io in Chrome — for Phase 2 browser automation
- Client name confirmed — all sequences/workflows will be prefixed with it

---

## Step 1 — Extract ICP from SPOT

Read the SPOT input. Pull from Tab 9 (Apollo Campaign Setup) or Tab 5 (ICP & Buyer Persona):

- Client name and domain
- Target titles (primary + secondary)
- Employee range
- Locations
- Industries
- Keyword passes
- Tech stack signals (positive and negative)
- Revenue range, funding stages, exclusions

If any critical field is `[TBD]`, flag it before running:

```
Missing fields — fill these in the SPOT before continuing:
- [field name]: needed for Apollo search
```

Critical: Target Titles, Employee Range, Locations, at least one Keyword Pass.

**Confirm the client name with the user** — this prefixes every sequence and workflow name.

---

## Step 2 — Build the Lead List (Automated via Apollo API)

Ask the user for their Apollo API key. Then execute the following Python code inline to search Apollo and export results as a CSV.

Run this code block — adapt the filter values based on what you extracted from the SPOT:

```python
import requests
import csv
import json

APOLLO_API_KEY = "PASTE_YOUR_API_KEY_HERE"
CLIENT_NAME = "[ClientName]"  # used for CSV filename

headers = {
    "X-Api-Key": APOLLO_API_KEY,
    "Content-Type": "application/json",
    "Cache-Control": "no-cache"
}

# Build search payload from SPOT ICP fields
# Adapt these values based on what you extracted in Step 1
search_payload = {
    "person_titles": [
        # From SPOT Tab 9 Target Titles (Primary + Secondary)
        # Example: "VP of Sales", "Head of Sales", "Sales Director"
    ],
    "person_seniorities": [
        # Include seniority levels that match your ICP
        # Options: owner, founder, c_suite, vp, director, manager, senior, entry, intern
        "vp", "director", "manager", "senior"
    ],
    "organization_num_employees_ranges": [
        # From SPOT Tab 9 Employee Range
        # Format: "min,max" — e.g. "11,50", "51,200", "201,500"
    ],
    "person_locations": [
        # From SPOT Tab 9 Locations
        # Example: "United States", "Canada"
    ],
    "organization_industry_tag_ids": [],  # fill if using industry tags
    "currently_using_any_of_technology_uids": [
        # From SPOT Tab 9 Tech Stack Signals (positive)
        # Apollo UIDs for tech signals — leave empty if unknown
    ],
    "q_keywords": "",  # optional: keyword search against contact/company descriptions
    "page": 1,
    "per_page": 100
}

all_contacts = []
page = 1
max_pages = 10  # cap at 1000 results; adjust if needed

print(f"Searching Apollo for {CLIENT_NAME} ICP...")

while page <= max_pages:
    search_payload["page"] = page
    response = requests.post(
        "https://api.apollo.io/api/v1/mixed_people/search",
        headers=headers,
        json=search_payload
    )

    if response.status_code != 200:
        print(f"Error on page {page}: {response.status_code} — {response.text[:200]}")
        break

    data = response.json()
    people = data.get("people", [])

    if not people:
        break

    all_contacts.extend(people)
    total = data.get("pagination", {}).get("total_entries", 0)
    print(f"Page {page}: {len(people)} results (total available: {total})")

    if len(all_contacts) >= total or len(people) < 100:
        break

    page += 1

print(f"\nTotal contacts fetched: {len(all_contacts)}")

# Export to CSV
filename = f"{CLIENT_NAME.lower().replace(' ', '_')}_apollo_leads.csv"
fields = ["first_name", "last_name", "title", "company", "email",
          "linkedin_url", "city", "state", "country", "phone_numbers"]

with open(filename, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for p in all_contacts:
        org = p.get("organization") or {}
        phones = p.get("phone_numbers") or []
        writer.writerow({
            "first_name": p.get("first_name", ""),
            "last_name": p.get("last_name", ""),
            "title": p.get("title", ""),
            "company": org.get("name", ""),
            "email": p.get("email", ""),
            "linkedin_url": p.get("linkedin_url", ""),
            "city": p.get("city", ""),
            "state": p.get("state", ""),
            "country": p.get("country", ""),
            "phone_numbers": "; ".join([ph.get("raw_number", "") for ph in phones])
        })

print(f"Exported to {filename}")
```

**Important notes:**
- The `mixed_people/search` endpoint is credit-free — it does not consume Apollo credits
- If you need verified emails, use `people/match` instead (costs credits)
- Run one keyword pass at a time for cleaner, more targeted lists
- Exclude competitor company employees by filtering the results or adding `organization_not_domains` if available

After the CSV exports, confirm:
```
Lead list exported: {n} contacts → {filename}
Review the CSV before adding contacts to sequences — spot-check titles and companies for fit.
```

---

## Step 3 — Create All 7 Sequences (Browser Automation)

Read `sequence_builder.py` — it contains the full step definitions for all 7 sequences and the execution guide in `EXECUTION_GUIDE`.

**Before starting:**
- Confirm Chrome is open and logged in at app.apollo.io
- Use `mcp__Claude_in_Chrome__navigate` to go to `https://app.apollo.io/#/sequences`
- Verify the page loads (not redirected to login)

**For each sequence 1–7 in `sequence_builder.RC_SEQUENCES`:**

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
8. Note the sequence ID from the URL for Step 4

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

## Step 4 — Create the 3 Workflow Plays (Browser Automation)

Read `workflow_builder.py` — it contains the full workflow definitions and execution guide in `EXECUTION_GUIDE`.

**Navigate** to `https://app.apollo.io/#/workflows`

**For each workflow 1–3 in `workflow_builder.RC_WORKFLOWS`:**

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

## Step 5 — Verification Checklist

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

LEAD LIST
[ ] CSV exported and spot-checked
[ ] Contact count confirmed with user
```

When all boxes are checked, the client is fully set up in Apollo and ready to run.
