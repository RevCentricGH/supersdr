---
name: tam-contact-mapper
description: Apply a client's ICP filters in Apollo's People tab and save the search as a named TAM view. Use when user says "map the TAM for [client]", "build the TAM for [client]", "save the Apollo search for [client]", or provides a SPOT doc and asks to set up the people search.
---

# TAM Contact Mapper

> **STATUS: LIVE-VALIDATED 2026-05-22.** The Apollo People UI references in `tam_filter_builder.py`'s `EXECUTION_GUIDE` were validated against the live Apollo UI via a Playwright DOM probe on 2026-05-22. Re-validate after any major Apollo UI release and bump the date in both files when you do. Still pending: a full end-to-end click-through that actually applies filters and clicks "Save as new search" inside Claude Cowork (where `mcp__Claude_in_Chrome__*` browser tools are available) — the probe only inspected and opened panels, it did not exercise the full save flow.

## Purpose

Reads a client's SPOT doc, extracts ICP filters, and applies them in Apollo's People tab using browser automation. Saves the filtered search as a named view — this is the broad TAM. No contacts are imported or enriched at this stage. The saved search is the output.

Run this skill after the SPOT doc is complete. The next step is `/list-builder` when you're ready to build a dial-ready enriched list from this TAM.

## Files

- `tam_filter_builder.py` — `FILTER_SCHEMA` mapping SPOT fields to Apollo filter sections + the `EXECUTION_GUIDE` constant the skill follows during browser automation

---

## What You Need Before Starting

- A completed SPOT doc (Google Doc URL) — if you don't have one, run `/client-spot` first
- Apollo open and logged in at app.apollo.io in Chrome
- Google Drive connector connected in Cowork (to read the SPOT doc)

---

## Getting started

When this skill is loaded, greet the user:

> "I'm the TAM Contact Mapper. I'll read your client's ICP from their SPOT doc and build a filtered People search in Apollo that maps their entire TAM — every contact that fits the ICP profile, with no contacts imported or touched. The output is a saved search in Apollo's People tab you can reference anytime.
>
> Paste your client's SPOT doc URL (Google Doc) and I'll take it from there."

Try to read the SPOT and navigate to Apollo immediately. Only raise issues if something actually fails.

**Failure handling:**
- **Google Drive read fails** → "Google Drive isn't connected. Go to Settings → Connectors → Google Drive, or paste Tab 5 and Tab 9 content directly."
- **Apollo isn't open or not logged in** → "Open Chrome, go to app.apollo.io, log in, then let me know."
- **Browser control not available** → "Computer Use isn't enabled. Go to Settings → Computer Use and turn it on."

---

## Step 1 — Read the SPOT doc

Use the Google Drive connector to read Tab 9 (Apollo Campaign Setup) and Tab 5 (ICP & Buyer Persona). Tab 9 is primary; fall back to Tab 5 for any field that's blank or `[TBD]`.

If the user pastes tab content directly, work from that.

---

## Step 2 — Extract ICP filters

| Field | What to look for |
|---|---|
| `client_name` | Client Name, Company Name |
| `target_titles` | Target Titles, Primary Titles, Job Titles |
| `seniority` | Seniority Level, Management Level |
| `employee_range` | Employee Range, Company Size — note min and max separately |
| `locations` | HQ Location, Geography, Countries |
| `industries` | Industries, Target Industries |
| `keywords` | Keywords, Keyword Passes |
| `tech_signals` | Tech Stack Signals, Technology |
| `funding_stages` | Funding Stages |
| `exclusions` | Exclusions, Competitor Domains |

**Block and do not proceed** if any of these are missing or `[TBD]`:
- Target Titles
- Employee Range
- Locations
- At least one of: Keywords or Industries

Tell the user which fields are missing and ask them to fill in Tab 9 before continuing.

---

## Step 3 — Confirm filters and search name

Print the extracted filters and default search name for the user to review:

```
Client:         {client_name}
Titles:         {target_titles}
Seniority:      {seniority}
Employee range: {employee_range}
Locations:      {locations}
Industries:     {industries}
Keywords:       {keywords}
Tech signals:   {tech_signals}
Funding stages: {funding_stages}
Exclusions:     {exclusions}

Search name: {client_name} - TAM - {YYYY-MM-DD}
```

Ask the user to confirm or provide a custom search name before proceeding.

---

## Step 4 — Apply filters in Apollo (Browser Automation)

Read `tam_filter_builder.py`. It contains:
- `FILTER_SCHEMA` — how each extracted SPOT field maps onto an Apollo filter section (UI type, include/exclude support, special toggles)
- `EXECUTION_GUIDE` — the ordered, step-by-step browser walkthrough (STEP A → STEP K)

Follow `EXECUTION_GUIDE` exactly. Use `mcp__Claude_in_Chrome__navigate` to open `https://app.apollo.io/#/people` and confirm the page loaded (not redirected to login) before STEP B.

**Verification checkpoints — run after EACH filter is applied:**

1. The corresponding active-filter pill appears above the results table
2. The result count drops (or changes) — if it does not change, the filter did not take and you must retry that filter before continuing
3. The sidebar section shows the filter as applied (check or count indicator)

If a verification fails twice in a row on the same filter, stop and screenshot before retrying. Do not skip filters silently.

**After all filters are applied:**

```
SPOT field         Apollo section               Applied   Result count after
-----------------  ---------------------------  --------  ------------------
Job Titles         Job Titles                    ✓         { … }
Seniority          Job Titles → Mgmt Levels      ✓         { … }
# Employees        # Employees                   ✓         { … }
Location           Location (Account HQ tab)     ✓         { … }
Industry           Industry & Keywords           ✓         { … }
Keywords           Industry & Keywords           ✓         { … }
Technologies       Technologies                  ✓         { … }
Funding            Funding                       ✓         { … }
Exclusions         per-section inline            ✓         { … }

Final TAM size: ~{N} contacts
```

Then proceed to STEP K (save the search) per `EXECUTION_GUIDE`.

---

## Step 5 — Confirm output

Report back:

```
TAM search saved.

Client:  {client_name}
Name:    {search_name}
Results: ~{N} contacts

View in Apollo → People tab → Saved Searches → {search_name}

Next: run /list-builder when you're ready to pull an enriched, dial-ready list from this TAM.
```

---

## Fallbacks

**0 results:** Tell the user which filters are likely too narrow — broaden in this order: # Employees → Location → Industry → Keywords. (Same order as `tam_filter_builder.py`'s EXECUTION_GUIDE STEP J.)

**Result count not updating after a filter is applied:** Apollo does not always auto-apply changes. Click "Apply Filters" at the top of the filter sidebar to force the update.

**Filter chip not found:** Some filters live under "More Filters" — click that to expand the full panel.

**Save search not available:** The user may be on a plan that doesn't support saved searches. They'd need to upgrade in Apollo settings.

---

## Voice Rules

Apply to all Claude-authored output — greetings, filter confirmations, status reports, error messages.

- No AI-tell openers: "Great question", "Absolutely", "Certainly", "Of course"
- No hedging: "I think", "it seems", "potentially", "it's worth noting"
- No AI vocabulary: "delve", "leverage", "utilize", "robust", "seamless", "comprehensive"
- No em-dashes. Hyphen or rewrite.
- Short. Direct. One idea per sentence.
