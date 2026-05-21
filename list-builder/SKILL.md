---
name: list-builder
description: Build an enriched, validated, signal-enriched dial-ready contact list. Pulls from an existing Apollo TAM saved search or runs fresh from a SPOT doc. Use when user says "build the list for [client]", "dial list for [client]", "enrich the TAM", "build a list from the TAM", or "build a contact list for [client]".
---

# List Builder

## Purpose

Builds a dial-ready contact list with enriched emails, phone numbers, validation, and signal context. This is the list SDRs actually work from — not a broad TAM view.

Two input modes:
- **TAM mode** (default): pulls from the client's existing saved TAM search in Apollo (`/tam-contact-mapper` output)
- **Direct mode** (fallback): runs fresh from the SPOT doc, bypassing the TAM entirely

Output: validated contacts with enriched contact data and signal notes, ready for sequences and dialing.

---

## What You Need Before Starting

- Apollo open and logged in at app.apollo.io in Chrome
- Google Drive connector connected (to read the SPOT doc if needed)
- Apollo API key (Settings → Integrations → API)
- Email validation API key — BounceBan or NeverBounce (optional but recommended)

---

## Getting started

When this skill is loaded, ask the user:

> "I'm the List Builder. I'll pull contacts from the TAM, enrich them with emails and phone numbers, validate, and add signal context.
>
> Two questions:
> 1. Are we building from the existing TAM saved search, or running fresh from the SPOT doc?
> 2. How many contacts do you want in this batch? (Recommended: start with 100–250 to validate the run before scaling)"

---

## Step 1 — Determine input mode

**TAM mode** (user says "from the TAM", "use the saved search", or it's implied):
- Ask for the saved search name (e.g. "Cekura - TAM - 2026-05-21") if not provided
- Confirm the client name

**Direct mode** (user says "from the SPOT", "skip the TAM", or TAM doesn't exist yet):
- Ask for the SPOT doc URL
- Proceed to Step 2a

---

## Step 2a — TAM mode: get contacts from Apollo (Browser Automation)

Navigate to the saved search and select a batch of contacts.

### EXECUTION_GUIDE — TAM mode

- Go to `https://app.apollo.io/#/people`
- Open Saved Searches (dropdown or sidebar) and select `{saved_search_name}`
- Confirm the filter is applied and results are visible
- Note the total result count
- Select the first `{batch_size}` contacts using the checkbox at the top (selects current page, 25 per page by default — page through and select until you have the target count)
- Click "Export" or note the contacts for passing to the enrichment script
  - If Apollo allows CSV export of selected contacts: export to `/tmp/{client_name}_raw.csv`
  - If not: note the page/filter state for the script to re-query via API

---

## Step 2b — Direct mode: extract ICP filters from SPOT

Read Tab 9 (primary) and Tab 5 (fallback) from the SPOT doc using the Google Drive connector.

Extract the same fields as `tam-contact-mapper`:
`client_name`, `target_titles`, `seniority`, `employee_range`, `locations`, `industries`, `keywords`, `tech_signals`, `funding_stages`, `exclusions`

Block if required fields are missing (same rules as `tam-contact-mapper`).

Confirm filters with user before proceeding.

---

## Step 3 — Run the enrichment and validation script

Get the Apollo API key from the user if not already provided.

Write the job config to `/tmp/{client_name}_job.json` and run `list_builder.py`:

```bash
python list_builder.py \
  --mode [tam|direct] \
  --client "{client_name}" \
  --batch-size {batch_size} \
  --filters /tmp/{client_name}_filters.json \   # direct mode only
  --raw-csv /tmp/{client_name}_raw.csv \         # tam mode only
  --api-key "{apollo_api_key}" \
  --email-validation-key "{bounceban_key}" \     # optional
  --output /tmp/{client_name}_list_{date}.csv
```

The script handles:
1. Apollo people enrichment (reveal emails + phones via Apollo's enrich API)
2. Email validation (BounceBan or NeverBounce — skipped if no key provided)
3. Phone validation (line type check — skipped if no Twilio creds)
4. Signal enrichment per company (job postings, recent news, tech stack context)
5. Output to structured CSV

---

## Step 4 — Relay the output

When the script finishes:

```
List build complete.

Client:             {client_name}
Contacts processed: {total}
Emails found:       {emails_found} ({email_pct}%)
Phones found:       {phones_found} ({phone_pct}%)
Emails valid:       {emails_valid} (skipped if no validation key)
Flagged / dropped:  {dropped}

Output: /tmp/{client_name}_list_{date}.csv

Columns: First Name, Last Name, Title, Company, Email, Email Status,
         Phone, Phone Type, LinkedIn URL, Signal Notes, Pain Score

Next steps:
- Review the CSV and spot-check 5–10 rows
- Upload to Smartlead or Apollo sequence
- Run /apollo-campaign-builder if sequences aren't set up yet
```

---

## Signal enrichment (per company)

For each unique company in the list, the script runs a lightweight signal pass:
- **Job postings**: what roles are they actively hiring? (hiring compliance, AI engineers, sales ops = buying signals)
- **Recent news/funding**: anything in the last 90 days that indicates growth, pain, or timing
- **Tech stack**: what tools are confirmed in their stack

This is written to the "Signal Notes" column as a 1–2 sentence summary per company. All contacts at the same company share the same signal note.

Signal enrichment runs via web search — no additional API keys required. It adds time (roughly 2–5s per unique company) so for large batches it runs in parallel where possible.

---

## Validation matrix

After enrichment, each contact is assigned one of these statuses:

| Status | Condition | Action |
|--------|-----------|--------|
| `READY` | Email valid + phone found | Include in output |
| `EMAIL_ONLY` | Valid email, no phone | Include — flag for email-first outreach |
| `PHONE_ONLY` | Phone found, email missing or invalid | Include — flag for call-first |
| `UNVERIFIED` | Email found but not validated (no key) | Include with note |
| `NO_CONTACT` | No email or phone found | Drop from output |
| `INVALID` | Email hard-bounced | Drop from output |

---

## Fallbacks

**Apollo enrichment returns no email/phone for many contacts:** This is normal — Apollo's hit rate varies by ICP. If hit rate is below 40%, suggest switching enrichment to BetterContact or FullEnrich waterfall (both integrate via API key — rerun with `--enrichment-tool bettercontact`).

**No email validation key:** Script proceeds without validation and marks all emails as `UNVERIFIED`. Recommend running validation before loading into sequences to protect sender reputation.

**Signal enrichment too slow:** Pass `--skip-signals` to produce a faster list without signal notes. Signals can be run as a separate pass later.

**Direct mode returns 0 results:** Filters may be too narrow — broaden Employee Range or Location and rerun.
