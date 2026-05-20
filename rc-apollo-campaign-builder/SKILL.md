---
name: rc-apollo-campaign-builder
description: Set up a new client's full Apollo campaign — build the initial lead list from SPOT ICP criteria and guide through creating all 7 outreach sequences and 3 workflow plays. Use when user says "set up Apollo for [client]", "build Apollo campaign for [client]", "run Apollo campaign builder", "build the list for [client]", or provides a SPOT doc and asks to set up outreach sequences.
---

# Apollo Campaign Builder

## Purpose

Two-phase skill for onboarding a new client into Apollo:

1. **Automated** — search Apollo's API by ICP criteria from the SPOT → export contacts as CSV
2. **Guided** — step-by-step creation of all 7 outreach sequences and 3 workflow plays in the Apollo UI

Run this skill after the SPOT doc is complete. Tab 9 (Apollo Campaign Setup) is the primary input.

---

## What You Need Before Starting

- SPOT doc (URL, PDF, uploaded file, or pasted content)
- Apollo API key (get it from Apollo → Settings → Integrations → API)
- Access to your Apollo account in a browser

---

## Step 1 — Extract ICP from SPOT

Read the SPOT input. Pull the following fields from Tab 9 (Apollo Campaign Setup) or Tab 5 (ICP & Buyer Persona) if Tab 9 isn't filled in:

- Keyword passes
- Employee range
- Revenue range
- Locations
- Industries
- Funding stages
- Target titles (primary + secondary)
- Tech stack signals (positive and negative)
- Exclusions (competitor companies, title keywords, company types)
- Client name and domain

If any critical field is `[TBD]`, flag it before running:

```
Missing fields — fill these in your SPOT before continuing:
- [field name]: needed for Apollo search
```

Critical fields: Target Titles, Employee Range, Locations, at least one Keyword Pass.

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

## Step 3 — Set Up the 7 Sequences in Apollo (Guided)

Apollo's API does not support creating sequences. You'll do this in the Apollo UI. Follow these steps exactly for each sequence.

**How to create a sequence in Apollo:**
1. In Apollo, go to **Sequences** in the left nav
2. Click **+ New Sequence**
3. Name it: `[ClientName] - [Sequence Name]` (e.g. "Acme Corp - Call Only")
4. Set sequence type to **Manual** or **Automatic** depending on the sequence
5. Add each step using the timing and type from the SOP below
6. Save and activate

Create all 7 sequences for the client. Work through them in order.

---

### Sequence 1: Call Only

Name: `[ClientName] - Call Only`

| Step | Type | Timing | Notes |
|------|------|--------|-------|
| 1 | Phone Call | Immediately | First dial |
| 2 | Phone Call | +3 hours | Second dial same day |
| 3 | Phone Call | +1 day | Third dial |
| 4 | Phone Call | +3 hours | Same-day follow-up |
| 5 | Phone Call | +1 day | Day 2 |
| 6 | Phone Call | +3 hours | Double-tap |
| 7 | Phone Call | +1 day | Continue rhythm |
| 8 | Phone Call | +3 hours | Re-attempt |
| 9 | Phone Call | +1 day | Re-engagement |
| 10 | Phone Call | +3 hours | Final push |

---

### Sequence 2: Activated Lead (Just Spoke)

Name: `[ClientName] - Activated Lead`

| Step | Type | Timing | Notes |
|------|------|--------|-------|
| 1 | Manual Email | Immediately | Personalized follow-up referencing the conversation |
| 2 | Phone Call | +2 days | First call to reconnect |
| 3 | Automatic Email | +5 days | Automated reminder with CTA to book |
| 4 | Phone Call | +3 days | Second call |
| 5 | Phone Call | +3 days | Third call |
| 6 | Phone Call | +3 days | Fourth call |
| 7 | Phone Call | +3 days | Final call — close or disqualify |

---

### Sequence 3: Nurture

Name: `[ClientName] - Nurture`

| Step | Type | Timing | Notes |
|------|------|--------|-------|
| 1 | Manual Email | Immediately | Personalized re-engagement |
| 2 | Automatic Email | +45 days | Light-touch automated check-in |
| 3 | Phone Call | +15 days | First call after email |
| 4 | Phone Call | +3 days | Second call |
| 5 | Phone Call | +3 days | Third call |
| 6 | Phone Call | +3 days | Fourth call |
| 7 | Phone Call | +15 days | Final attempt — close loop |

---

### Sequence 4: Cold Follow-Up

Name: `[ClientName] - Cold Follow-Up`

| Step | Type | Timing | Notes |
|------|------|--------|-------|
| 1 | Phone Call | Immediately | First attempt |
| 2 | Phone Call | +3 hours | Same-day retry |
| 3 | Phone Call | +1 day | Next day |
| 4 | Phone Call | +3 hours | Same-day retry |
| 5 | Phone Call | +1 day | Continue |
| 6 | Phone Call | +3 hours | Double-tap |
| 7 | Phone Call | +1 day | Next day |
| 8 | Phone Call | +3 hours | Retry |
| 9 | Phone Call | +1 day | Continue |
| 10 | Phone Call | +3 hours | Retry |
| 11 | Phone Call | +1 day | Continue |
| 12 | Phone Call | +3 hours | Retry |
| 13 | Phone Call | +1 day | Final scheduled attempt |
| 14 | Phone Call | +3 hours | Last push before inactive |

---

### Sequence 5: Pending Meeting

Name: `[ClientName] - Pending Meeting`

| Step | Type | Timing | Notes |
|------|------|--------|-------|
| 1 | Manual Email | +30 minutes after booking | Confirmation email with meeting details and instructions |
| 2 | Action Item | Immediately | Internal reminder: confirm the meeting the day before, send a confirmation message, and call the day before |

---

### Sequence 6: Reschedule

Name: `[ClientName] - Reschedule`

| Step | Type | Timing | Notes |
|------|------|--------|-------|
| 1 | Phone Call | Immediately | First rebooking attempt |
| 2 | Phone Call | +1 day | Follow-up |
| 3 | Phone Call | +1 day | Second follow-up |
| 4 | Phone Call | +1 day | Third follow-up |
| 5 | Phone Call | +1 day | Fourth follow-up |
| 6 | Phone Call | +3 days | Re-engagement attempt |
| 7 | Phone Call | +3 days | Continue |
| 8 | Phone Call | +3 days | Second re-engagement |
| 9 | Phone Call | +3 days | Final attempt |
| 10 | Phone Call | +3 days | Close out |

---

### Sequence 7: Referred To

Name: `[ClientName] - Referred To`

| Step | Type | Timing | Notes |
|------|------|--------|-------|
| 1 | Phone Call | Immediately | First attempt |
| 2 | Phone Call | +1 day | Follow-up |
| 3 | Phone Call | +1 day | Second follow-up |
| 4 | Phone Call | +1 day | Third follow-up |
| 5 | Phone Call | +1 day | Fourth follow-up |
| 6 | Phone Call | +3 days | Re-engagement |
| 7 | Phone Call | +3 days | Continue |
| 8 | Phone Call | +3 days | Second re-engagement |
| 9 | Phone Call | +3 days | Final attempt |
| 10 | Phone Call | +3 days | Close out |

---

## Step 4 — Set Up the 3 Workflow Plays in Apollo (Guided)

Workflows in Apollo trigger automatic actions when a contact disposition is updated. Create these 3 plays for the client.

**How to create a workflow play in Apollo:**
1. In Apollo, go to **Workflows** (or **Plays**) in the left nav
2. Click **+ New Play** (or **+ Create Workflow**)
3. Set the trigger condition
4. Add each action in order
5. Make sure the sequence filter points to THIS client's sequences — not another client's
6. Save and activate

**CRITICAL:** When adding a "Add to Sequence" action, always select the client-specific sequence you just created (e.g. `[ClientName] - Activated Lead`). Never leave it pointed at a generic or previous client's sequence. This is the most common setup error.

---

### Play 1: Disposition → Activated Lead

Trigger: Contact disposition is set to **Activated Lead**

Actions (in order):
1. Add contact to sequence: `[ClientName] - Activated Lead`
2. Create a Deal in Apollo CRM under status "Activated Lead"
3. Associate the contact to the deal

---

### Play 2: Disposition → Nurture

Trigger: Contact disposition is set to **Nurture**

Actions (in order):
1. Add contact to sequence: `[ClientName] - Nurture`

---

### Play 3: Disposition → Meeting Booked

Trigger: Contact disposition is set to **Meeting Booked**

Actions (in order):
1. Add contact to list: `[ClientName] - Meetings Booked`
2. Add contact to sequence: `[ClientName] - Pending Meeting`

---

## Step 5 — Verification Checklist

After completing Steps 3 and 4, confirm each item:

```
SEQUENCE SETUP
[ ] Sequence 1 (Call Only) created with 10 steps
[ ] Sequence 2 (Activated Lead) created with 7 steps
[ ] Sequence 3 (Nurture) created with 7 steps
[ ] Sequence 4 (Cold Follow-Up) created with 14 steps
[ ] Sequence 5 (Pending Meeting) created with 2 steps
[ ] Sequence 6 (Reschedule) created with 10 steps
[ ] Sequence 7 (Referred To) created with 10 steps
[ ] All sequences prefixed with [ClientName]

WORKFLOW SETUP
[ ] Play 1 (Activated Lead) triggers on correct disposition
[ ] Play 1 adds to [ClientName] - Activated Lead sequence (not another client's)
[ ] Play 1 creates a Deal and associates the contact
[ ] Play 2 (Nurture) triggers on correct disposition
[ ] Play 2 adds to [ClientName] - Nurture sequence
[ ] Play 3 (Meeting Booked) triggers on correct disposition
[ ] Play 3 adds to [ClientName] - Meetings Booked list
[ ] Play 3 adds to [ClientName] - Pending Meeting sequence

LEAD LIST
[ ] CSV exported with contacts matching ICP criteria
[ ] Spot-checked — titles and companies look right
[ ] Ready to import or upload to sequences
```

Once all boxes are checked, the client is set up in Apollo and ready to run.
