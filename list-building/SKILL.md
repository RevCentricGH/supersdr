---
name: list-building
description: Read a client's SPOT doc and build a named Apollo contact list from their ICP filters. Use when user says "build a list", "build a contact list", "build an Apollo list", "list build", "build the list for [client]", "[client] list", or pastes a SPOT doc URL and asks to build contacts.
---

# List Building

## Purpose

Reads a client's SPOT Google Doc, extracts ICP filters from Tab 5 (ICP & Buyer Persona) and Tab 9 (Apollo Campaign Setup), searches Apollo for matching people, and creates a named contact list in the user's Apollo workspace.

Run this skill after the SPOT doc is complete. The output is one Apollo contact list ready for sequences. The next step after this skill is `apollo-campaign-builder`.

## Files

- `list_builder.py` — Python script that reads the SPOT, runs the Apollo search, and creates the contact list

---

## What You Need Before Starting

- A completed SPOT doc (Google Doc URL) — if you don't have one, run `/client-spot` first
- Apollo paid plan with API access (Settings → Integrations → API)
- Google Docs auth already set up (same credentials used by the `gdocs.py` CLI)

---

## Step 1 — Get the SPOT doc URL

Ask the user to paste the SPOT Google Doc URL if they haven't already. The URL should look like:
`https://docs.google.com/document/d/XXXX/edit`

If no SPOT exists yet, stop and say:

> "Run `/client-spot` first to generate a SPOT for this client, then come back to build the list."

---

## Step 2 — Read Tab 5 + Tab 9, extract ICP filters

Run `list_builder.py` — it will read the SPOT automatically. The script extracts:

| Field | Source |
|---|---|
| Target Titles | Tab 9 → Tab 5 fallback |
| Employee Range | Tab 9 → Tab 5 fallback |
| Locations | Tab 9 → Tab 5 fallback |
| Industries | Tab 9 → Tab 5 fallback |
| Keyword Passes | Tab 9 → Tab 5 fallback |
| Tech Stack Signals | Tab 9 → Tab 5 fallback |
| Exclusion Domains | Tab 9 → Tab 5 fallback |
| Funding Stages | Tab 9 → Tab 5 fallback |

The script prints every field it found so the user can verify before the search runs.

---

## Step 3 — Validate critical fields

The script blocks and exits if any of these are missing or `[TBD]` in the SPOT:

- Target Titles
- Employee Range
- Locations
- At least one of: Keyword Passes or Industries

If the script exits with missing fields, tell the user:

> "Fill in the missing fields in the SPOT doc and re-run. Tab 9 (Apollo Campaign Setup) is the primary source — Tab 5 (ICP & Buyer Persona) is the fallback."

---

## Step 4 — Confirm filters and list name

The script shows the extracted filters and prompts the user to confirm before running the search. The default list name is:

```
{Client Name} - Contacts - {YYYY-MM-DD}
```

The user can type a custom name or press Enter to accept the default.

---

## Step 5 — Apollo API key

The script checks for `APOLLO_API_KEY` in the environment and in a local `.env` file first. If not found, it prompts the user to paste their key. After entry it offers to save it to `.env` for future runs.

To find the API key: Apollo → Settings → Integrations → API → copy the key.

---

## Step 6 — Run the script

```bash
python list_builder.py --spot-url "<SPOT URL>"
```

Or fully non-interactive if all args are known:

```bash
python list_builder.py \
  --spot-url "<SPOT URL>" \
  --list-name "<List Name>" \
  --api-key "<Apollo API Key>"
```

The script paginates through all Apollo results automatically. For large lists (1,000+ contacts) this may take a minute — a progress line prints for each page.

---

## Step 7 — Output

When the script finishes it prints:

```
✓ Read SPOT for {Client Name}
✓ Extracted ICP filters
✓ Apollo people search: {N} results
✓ Created list: {List Name}
✓ Added {N} contacts

View in Apollo: https://app.apollo.io/#/contacts

Next step: run /apollo-campaign-builder to set up sequences and workflows for this list.
```

Relay this output to the user and confirm the list is visible in Apollo before closing.

---

## Output format

The final message to the user should follow this exact template:

```
List build complete.

Client: {Client Name}
List name: {List Name}
Contacts added: {N}

View in Apollo → https://app.apollo.io/#/contacts (filter by list name to confirm)

Next: run /apollo-campaign-builder to create the 7 sequences and 3 workflow plays for this client.
```

---

## Fallback

If the SPOT doc URL returns a permission error or cannot be read, tell the user:

> "Make sure the doc is shared with anyone with the link (or that your Google account has access), then try again."

If Apollo returns 0 results, tell the user:

> "No contacts found matching these filters. The ICP may be too narrow — check Employee Range, Locations, and Keywords in Tab 9 of the SPOT and broaden at least one filter."

If Apollo returns a 401 error, tell the user:

> "Invalid API key. Go to Apollo → Settings → Integrations → API and copy the key again."
