---
name: tam-contact-mapper
description: Apply a client's ICP filters in Apollo's People tab and save the search as a named TAM view. Requires a completed SPOT doc as the ICP source. Maps the TAM only. No contacts are imported or enriched. Use when user says "map the TAM for [client]", "build the TAM for [client]", "save the Apollo search for [client]", or provides a SPOT doc and asks to set up the people search.
# capabilities is free-form prose for human readers and harness docs, not a schema-backed list
capabilities: call the Apollo REST API, read a Google Doc
---

# TAM Contact Mapper

## Purpose

Reads a client's SPOT doc, extracts ICP filters, builds a filtered People search via the Apollo REST API, and saves it as a named view - this is the broad TAM. No contacts are imported or enriched at this stage. The saved search is the output.

Run this skill after the SPOT doc is complete. The next step is `/list-builder` when you're ready to build a dial-ready enriched list from this TAM.

## Files

- `tam_filter_builder.py` - `FILTER_SCHEMA` mapping SPOT fields to Apollo filter sections; use it to translate each extracted field into the matching Apollo filter parameter. The file also contains a legacy `EXECUTION_GUIDE` browser walkthrough that this skill does not follow.

The `.py` file is data the skill reads at runtime - not a script to run, not a doc to edit.

---

## Prerequisites

- A completed SPOT doc (Google Doc URL or pasted tab content) - if you don't have one, run `/client-spot` first
- `APOLLO_API_KEY` set in your environment
- An HTTP client capability and a way to read Google Docs

---

## Getting started

When this skill is loaded, greet the user:

> "I'm the TAM Contact Mapper. I'll read your client's ICP from their SPOT doc and build a filtered People search in Apollo that maps their entire TAM (Total Addressable Market) - every contact that fits the ICP profile, with no contacts imported or touched. The output is a saved search in Apollo's People tab you can reference anytime.
>
> One pause before I hit Apollo: I'll show you the extracted filters and the search name for confirmation before applying anything. After that it runs on its own.
>
> Paste your client's SPOT doc URL (Google Doc) and I'll take it from there."

Try to read the SPOT and proceed immediately. Only raise issues if something actually fails.

**Failure handling:**
- **SPOT doc unreadable** → "Can't access that doc. Paste Tab 5 (ICP & Buyer Persona) and Tab 9 (Apollo Campaign Setup) content directly."
- **API key not set** → "APOLLO_API_KEY isn't configured. Set APOLLO_API_KEY in your environment before running this skill."
- **No HTTP client capability** → stop and tell the user which capability is missing. There is no fallback path.

---

## Step 1 - Read the SPOT doc

Read the SPOT doc using your file-access capability: Tab 9 (Apollo Campaign Setup) and Tab 5 (ICP & Buyer Persona). Tab 9 is primary; fall back to Tab 5 for any field that's blank or `[TBD]` (to be determined - left unfilled by client-spot).

If the user pastes tab content directly, work from that.

---

## Step 2 - Extract ICP filters

| Field | What to look for |
|---|---|
| `client_name` | Client Name, Company Name |
| `target_titles` | Target Titles, Primary Titles, Job Titles |
| `seniority` | Seniority Level, Management Level |
| `employee_range` | Employee Range, Company Size - note min and max separately |
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

## Step 3 - Confirm filters and search name

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

## Step 4 - Build and save the search via the Apollo REST API

Bind your HTTP client to the Apollo REST API at api.apollo.io.

**Goal:** Save a TAM search in Apollo matching the confirmed ICP filters.

1. Map each extracted field to its Apollo filter parameter using `FILTER_SCHEMA` in `tam_filter_builder.py`.
2. Query the Apollo People search API with the mapped filters to get the TAM result count.
   - If the result count is 0, stop and suggest broadening (see Fallbacks).
3. Build a collision-resistant search name: take the name the user confirmed in Step 3 and append a short UUID or timestamp (e.g. `{client_name} - TAM - {YYYY-MM-DD} - {a1b2c3}`). Concurrent runs and retries must never produce two searches with the same name.
4. Call the Apollo save-search API endpoint with the collision-resistant name and the filter payload. Record the saved-search ID from the response.
5. Verify the saved search via the Apollo API, bound to the saved-search ID returned in step 4 - never match by name string.

**Rate-limit and retry rules:**
- On a 429 response, stop immediately and surface the rate-limit error to the user. Do not retry automatically.
- After an ambiguous timeout or network failure on the save-search call, do not silently re-attempt the save - the write may already have succeeded. Tell the user "save may or may not have succeeded - verify in Apollo directly" and halt. Explicit retry is the user's decision.

If the API call fails and you lack an HTTP client capability, stop and tell the user which capability is missing. There is no browser or manual-automation fallback; the REST API path is the only path.

---

## Step 5 - Confirm output

Report "TAM search saved" only after the ID-bound verification in Step 4 confirms the saved search exists. If verification fails, do not print this report - use the failure branch below.

Once verified, report back:

```
TAM search saved.

Client:  {client_name}
Name:    {search_name}
Results: ~{N} contacts

View in Apollo → People tab → Saved Searches → {search_name}

Next: run /list-builder when you're ready to pull an enriched, dial-ready list from this TAM.
```

**Failure branch.** Give the user an explicit error message for each of these cases:

- **Non-2xx API response** (general)
- **401/403** - auth failure; the API key is missing, wrong, or lacks permission
- **429** - rate-limited; stopped without retrying (per Step 4 rules)
- **422** - malformed filter payload; name the filter field Apollo rejected if the response identifies it
- **Save-search failure** - the save call failed or verification could not confirm the saved-search ID

Every error message must redact `APOLLO_API_KEY`, authorization headers, request URLs, and raw response bodies before anything is shown to the user. Each message must still carry safe diagnostics:

- Sanitized HTTP status code
- Apollo error category (from the response body, if available)
- Request operation name (e.g. "people-search", "save-search", "verify-search")
- Saved-search ID, when available
- A short correlation note (step number and timestamp) so concurrent runs can be told apart

In every failure case, also hand the user the filter payload from Step 3 so they can save the search manually in Apollo.

---

## Fallbacks

**0 results:** Tell the user which filters are likely too narrow - broaden in this order: # Employees → Location → Industry → Keywords.

**422 invalid filter value:** Apollo didn't recognize a value. Try one variant of the title or industry name and retry once. If it fails again, report per the failure branch.

**Save search not available:** The user may be on an Apollo plan that doesn't support saved searches. They'd need to upgrade in Apollo settings.

---

## Voice Rules

Apply to all skill content - this file, `tam_filter_builder.py`, and every Claude-authored response (greetings, filter confirmations, status reports, error messages). No em-dashes anywhere.

- No AI-tell openers: "Great question", "Absolutely", "Certainly", "Of course"
- No hedging: "I think", "it seems", "potentially", "it's worth noting"
- No AI vocabulary: "delve", "leverage", "utilize", "robust", "seamless", "comprehensive"
- No em-dashes. Hyphen or rewrite.
- Short. Direct. One idea per sentence.
