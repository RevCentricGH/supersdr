---
name: list-building
description: Read a client's SPOT doc and build a named Apollo contact list from their ICP filters. Use when user says "build a list", "build a contact list", "build an Apollo list", "list build", "build the list for [client]", "[client] list", or pastes a SPOT doc URL and asks to build contacts.
---

# List Building

## Purpose

Reads a client's SPOT Google Doc, extracts ICP filters from Tab 5 (ICP & Buyer Persona) and Tab 9 (Apollo Campaign Setup), searches Apollo for matching people, and creates a named contact list in the user's Apollo workspace.

Run this skill after the SPOT doc is complete. The output is one Apollo contact list ready for sequences. The next step is `apollo-campaign-builder`.

## Files

- `list_builder.py` — Python script that runs the Apollo search and creates the contact list. Claude runs this inside the Cowork VM after extracting ICP from the SPOT.

---

## What You Need Before Starting

- A completed SPOT doc (Google Doc URL) — if you don't have one, run `/client-spot` first
- Apollo paid plan with API access (Settings → Integrations → API → copy the key)
- Google Drive connector connected in Claude Cowork (Settings → Connectors → Google Drive) — needed to read the SPOT doc

---

## Getting started

When this skill is loaded, greet the user:

> "I'm the List Building skill. I'll search Apollo and build a named contact list for your client based on their ICP — that's the profile of the ideal company and person to target, pulled from their SPOT doc (their campaign knowledge base).
>
> Before we start, I need to check two things."

**Check 1 — Google Drive connector:**

> "First: is your Google Drive connected in Cowork? I need this to read your SPOT doc. Go to Settings → Connectors → Google Drive and connect your Google account if you haven't already. Let me know once it's connected — or if you'd rather paste the contents of Tab 5 and Tab 9 from your SPOT directly, that works too."

Wait for confirmation before moving on.

**Check 2 — Apollo API key:**

> "Second: do you have your Apollo API key? You'll find it in Apollo under Settings → Integrations → API. Paste it here and I'll use it for this session."

Once both are confirmed, ask:

> "Great — paste your SPOT doc URL and I'll take it from there."

Walk through each check one at a time. Don't list both at once and don't move past a blocker until it's resolved.

---

## Step 1 — Get the SPOT doc URL

Ask the user to paste the SPOT Google Doc URL if they haven't already.

If the Google Drive connector is not connected, say:

> "To read the SPOT doc automatically, connect Google Drive in Cowork Settings → Connectors → Google Drive. Or paste the content of Tab 5 and Tab 9 directly and I'll extract the filters from that."

---

## Step 2 — Read Tab 5 and Tab 9

Use the Google Drive connector to read the SPOT doc. Pull the full text of:

- **Tab 9 (Apollo Campaign Setup)** — primary source for all ICP filters
- **Tab 5 (ICP & Buyer Persona)** — fallback if Tab 9 fields are missing

If the user pasted tab content directly instead, work from that.

---

## Step 3 — Extract ICP filters

From the tab text, extract these fields. Tab 9 is the primary source; fall back to Tab 5 for any field that is blank or `[TBD]`.

| Field | What to look for |
|---|---|
| `client_name` | Client Name, Company Name |
| `target_titles` | Target Titles, Primary Titles, Job Titles |
| `employee_range` | Employee Range, Company Size — parse into `"min,max"` format (e.g. `"11,500"`) |
| `locations` | Locations, Geography, Countries |
| `industries` | Industries, Target Industries |
| `keywords` | Keyword Passes, Keywords |
| `tech_signals` | Tech Stack Signals, Technology |
| `exclusions` | Exclusions, Competitor Domains |
| `funding_stages` | Funding Stages, Funding Stage |

**Block and do not proceed** if any of these are missing or still `[TBD]`:
- Target Titles
- Employee Range
- Locations
- At least one of: Keywords or Industries

If blocked, tell the user which fields are missing and ask them to fill in the SPOT (Tab 9) before continuing.

---

## Step 4 — Show filters and confirm

Print the extracted filters and the default list name for the user to review:

```
Client:         {client_name}
Titles:         {target_titles}
Employee range: {employee_range}
Locations:      {locations}
Keywords:       {keywords}
Industries:     {industries}
Tech signals:   {tech_signals}
Exclusions:     {exclusions}
Funding stages: {funding_stages}

Default list name: {client_name} - Contacts - {YYYY-MM-DD}
```

Ask the user to confirm or provide a custom list name before proceeding.

---

## Step 5 — Get the Apollo API key

Ask the user for their Apollo API key if they haven't provided it.

> "Paste your Apollo API key — find it at: Apollo → Settings → Integrations → API"

---

## Step 6 — Run the script

Claude handles this step automatically — you don't need to run anything. Claude will write the ICP filters to a temporary file and run `list_builder.py` in the background inside Cowork. You'll see progress lines as it pages through Apollo results.

The JSON file written to `/tmp/icp_filters.json` should match this shape:

```json
{
  "target_titles": ["VP of Sales", "Head of Sales"],
  "employee_range": ["11,500"],
  "locations": ["United States", "Canada"],
  "keywords": ["B2B SaaS", "outbound sales"],
  "industries": ["Software", "Technology"],
  "tech_signals": ["Salesforce", "HubSpot"],
  "exclusions": ["competitor.com"],
  "funding_stages": ["Series A", "Series B"]
}
```

Omit any field that is empty — don't pass empty arrays.

The script paginates through all Apollo results automatically and prints a progress line per page. For large lists (1,000+ contacts) this may take a minute.

---

## Step 7 — Relay the output

When the script finishes, relay this to the user:

```
List build complete.

Client: {client_name}
List name: {list_name}
Contacts added: {N}

View in Apollo → https://app.apollo.io/#/contacts
(Filter by list name to see the contacts)

Next: run /apollo-campaign-builder to create the 7 sequences and 3 workflow plays for this client.
```

---

## Fallbacks

**Google Drive connector not set up:** Ask the user to paste Tab 5 and Tab 9 content directly.

**0 results from Apollo:** Tell the user:
> "No contacts found with these filters — the ICP may be too narrow. Check Employee Range, Locations, and Keywords in Tab 9 and broaden at least one filter."

**Apollo 401 error:** Tell the user:
> "Invalid API key. Go to Apollo → Settings → Integrations → API and copy the key again."

**Missing SPOT doc:** Tell the user:
> "Run `/client-spot` first to generate a SPOT for this client, then come back to build the list."
