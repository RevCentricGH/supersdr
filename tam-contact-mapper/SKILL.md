---
name: tam-contact-mapper
description: Apply a client's ICP filters in Apollo's People tab and save the search as a named TAM view. Use when user says "map the TAM for [client]", "build the TAM for [client]", "save the Apollo search for [client]", or provides a SPOT doc and asks to set up the people search.
---

# TAM Contact Mapper

## Purpose

Reads a client's SPOT doc, extracts ICP filters, and applies them in Apollo's People tab using browser automation. Saves the filtered search as a named view — this is the broad TAM. No contacts are imported or enriched at this stage. The saved search is the output.

Run this skill after the SPOT doc is complete. The next step is `/list-builder` when you're ready to build a dial-ready enriched list from this TAM.

---

## What You Need Before Starting

- A completed SPOT doc (Google Doc URL) — if you don't have one, run `/client-spot` first
- Apollo open and logged in at app.apollo.io in Chrome
- Google Drive connector connected in Cowork (to read the SPOT doc)

---

## Getting started

When this skill is loaded, greet the user:

> "I'm the TAM Contact Mapper. I'll apply your client's ICP filters in Apollo and save the search as a named TAM view.
>
> Paste your SPOT doc URL and I'll take it from there."

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

Navigate to `https://app.apollo.io/#/people`. Apply filters in this order using the EXECUTION_GUIDE below.

### EXECUTION_GUIDE

**Navigate to People tab**
- Go to `https://app.apollo.io/#/people`
- Wait for the page to load and the filter bar to appear

**Job Titles**
- Click the "Job Titles" filter chip
- For each title in `target_titles`: type the title → select from the autocomplete dropdown
- Click away or press Escape to close

**Seniority** (if provided)
- Click the "Seniority" filter chip
- Check each matching level (e.g. Director, VP, C-Suite, Manager, Owner)
- Click away to close

**Employee Count**
- Click the "# Employees" filter chip
- Enter the min and max values from `employee_range`
- Confirm the range

**Location** (Company HQ)
- Click the "Location" filter chip
- Select "Company HQ Location" (not person location) if given the choice
- For each location: type → select from dropdown
- Click away to close

**Industry** (if provided)
- Click the "Industry" filter chip
- For each industry: type → select from dropdown
- Click away to close

**Technologies** (if `tech_signals` provided)
- Click the "Technologies" filter chip
- For each technology: type → select from dropdown
- Use "Currently uses any of" (not "all of")
- Click away to close

**Funding Stage** (if provided)
- Click the "Funding Stage" filter chip
- Check each matching stage
- Click away to close

**Keywords** (if provided)
- Click the "Keywords" filter chip
- Enter keywords
- Click away to close

**Exclusions** (if provided)
- Look for "Exclude" options — may be under "More Filters"
- Find domain exclusion and enter each exclusion domain
- Click away to close

**Review result count**
- Note the total contact count shown at the top of the results
- If 0 results: stop and report back — suggest broadening Employee Range or Location first
- If results look reasonable, proceed to save

**Save the search**
- Click "Save search" or "Save as new search" (top right of the People search area)
- Enter the name: `{client_name} - TAM - {YYYY-MM-DD}`
- Confirm/Save
- Verify it appears in the saved searches list

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

**0 results:** Tell the user which filters are likely too narrow — start with Employee Range, then Location, then Industry.

**Filter chip not found:** Some filters live under "More Filters" — click that to expand the full panel.

**Save search not available:** The user may be on a plan that doesn't support saved searches. They'd need to upgrade in Apollo settings.
