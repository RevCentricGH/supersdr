---
name: weekly-checkin
description: Claude Code skill - runs in a terminal with real Python and local credentials, not in Cowork. Build a weekly client-delivery digest for one ISO week. It reads each client's call and disposition rows from the master-tracker Google Sheet and pulls their SmartLead campaign stats, then prints a per-client section with the call count, a disposition breakdown, and SmartLead sent, open rate, reply rate, and bounce count. Trigger when the user wants a weekly client check-in or delivery report, a per-client outbound summary, or says things like "run weekly-checkin", "build the weekly digest", "weekly client report for week 2026-W22", or "how did each client do this week". Runs on demand for one ISO week (YYYY-WNN, Monday-anchored). It only reads the sheet, never writes to it. SmartLead stats are fetched per campaign with 429-aware backoff and are omitted rather than mislabeled when the API cannot confirm the weekly date range. Per-student credentials (your SmartLead API key and Google OAuth); nothing is hardcoded.
---

# weekly-checkin

> **Claude Code skill - runs in a terminal, NOT Cowork.** This skill is real Python that needs
> a shell, the filesystem, a local SmartLead API key, and a Google OAuth token file. Do not
> upload it into the Cowork desktop app. Run it from a terminal with `python3 run.py --week ...`.

Build a weekly client-delivery digest. For a given ISO week, it reads the call and disposition
rows master-tracker wrote to your Google Sheet and pulls each client's SmartLead campaign stats,
then prints one section per client: how many calls, the disposition breakdown, and the SmartLead
sent count, open rate, reply rate, and bounce count for that week.

It is read-only on the sheet. It never writes a row, so a bad run cannot corrupt the
master-tracker data; a mid-run abort leaves nothing to clean up.

## What it does on each run

1. Resolves the `--week` you pass (`YYYY-WNN`, ISO 8601, Monday-anchored) into a Monday..Sunday
   date range.
2. Reads each client's `rep_tabs` from the master-tracker Google Sheet, keeping only the rows
   whose `Date` falls in that week. Rows with an empty `Date` or `Disposition` are skipped.
3. Pulls SmartLead campaign stats for each client's `smartlead_campaign_ids`, scoped to the
   week's date range, with 429-aware backoff.
4. Builds one digest section per client (call count, disposition breakdown, per-campaign stats)
   and prints it.

Run it again any time. It reads live data each run, so re-running is safe and always current.

## Prerequisites

This digest is only as fresh as the master-tracker sheet. **Run master-tracker first** so the
week's calls are actually in the sheet. If master-tracker has not synced that week yet, the
sheet rows are empty and the digest shows zeros (not an error).

## Setup

This is a one-time setup per operator. Everything runs on your own accounts. Your filled-in
config and your secrets are gitignored: `config.json`, `credentials.json`, and `token.json` are
listed in `weekly-checkin/.gitignore` and must never be committed. The committed
`config.template.json` carries only placeholders.

1. **Install dependencies** (Python 3.10+):

   ```
   cd weekly-checkin
   python3 -m pip install -r requirements.txt
   ```

2. **Create your config.** Copy the template and fill it in.

   ```
   cp config.template.json config.json
   ```

   Fields:
   - `smartlead_api_key` - your SmartLead API key (SmartLead Settings -> API). Sent as the
     `api_key` query param on every request; nothing is hardcoded.
   - `google_sheet_id` - the ID of the master-tracker sheet from its URL
     (`.../spreadsheets/d/<THIS>/edit`).
   - `google_oauth.credentials_file` / `google_oauth.token_file` - paths to your Google OAuth
     client secret and the token file the skill writes after the first authorization.
   - `clients` - a non-empty array, one entry per client:
     - `name` - the client name, used as the section title.
     - `rep_tabs` - the master-tracker tab names whose calls belong to this client.
     - `smartlead_campaign_ids` - the SmartLead campaign IDs to report for this client.
     Every `rep_tab` and every `smartlead_campaign_id` must belong to exactly one client. A
     duplicate across clients fails at startup with the duplicated value named.

3. **Set up Google OAuth.** In Google Cloud Console, enable the Google Sheets API, create an
   OAuth client (Desktop app), download the client secret JSON, and point `credentials_file` at
   it. The first run opens a browser to authorize and writes `token_file` for later runs. The
   skill requests read-only Sheets access.

4. **Share the sheet** with the Google account you authorize.

## Run

```
python3 run.py --week 2026-W22                       # uses ./config.json
python3 run.py --week 2026-W22 --config /path/to/config.json
```

Pass the ISO week you want. It prints a per-client digest to stdout. Scheduling and delivery are
out of scope here; this is an on-demand run for one week.

## How it is built

The logic lives in the `weeklycheckin` package and is unit-tested:

- `week_filter.py` - `week_bounds`: turns `YYYY-WNN` into a Monday..Sunday `date` pair.
- `config.py` - `load_config` / `validate_config`: fail-fast config validation and cross-client
  `rep_tab` / `smartlead_campaign_id` uniqueness.
- `sheet_reader.py` - `SheetReader`: reads a rep tab's rows for the week from an injected Sheets
  service; strips header whitespace; fails fast on a missing tab, a missing `Date`/`Disposition`
  column, or an unparseable date.
- `digest_builder.py` - `DigestBuilder`: joins the sheet rows and the SmartLead stats into one
  section per client; `render_digest` formats the sections for printing.

The side-effecting wrappers are kept thin and validated by the manual end-to-end run:

- `smartlead_client.py` - `SmartLeadClient`: per-campaign stats with 429-aware backoff, a
  30-second per-request timeout, and a closed-default date-range check (see below).
- `run.py` - wires the Google OAuth flow, the live clients, and prints the digest.

Run the tests from the repo root:

```
python3 -m pytest weekly-checkin
```

## SmartLead date-range safety

SmartLead's `/statistics` endpoint may return lifetime campaign aggregates rather than figures
scoped to the week. `weekly-checkin` fails closed: it accepts the numbers only when the response
carries a per-day breakdown or echoes back `start_date`/`end_date` matching the requested week.
Otherwise it raises rather than label lifetime totals as weekly. A campaign the API has no data
for prints a named warning to stderr and is left out of the digest, not silently zeroed.

## Troubleshooting

| Symptom | Likely cause and fix |
| --- | --- |
| Digest shows zeros for every client | The week's calls are not in the sheet yet. Run master-tracker for that week first, then re-run. Also confirm the `rep_tabs` names match the master-tracker tab names exactly. |
| `configured rep_tab '...' does not exist in the sheet` | A `rep_tabs` entry does not match a tab name in the master-tracker sheet. Fix the name in `config.json` to match the tab exactly. |
| `tab '...' is missing the 'Date'/'Disposition' column` | The master-tracker header drifted. Confirm the rep tabs still have `Date` and `Disposition` header cells. |
| SmartLead stats omitted with a warning on stderr | The API returned no data for that campaign and week, or could not confirm the date range. Confirm the campaign ID and that the campaign has activity that week. |
| Auth fails or asks to re-authorize every run | The OAuth token expired or was revoked. Delete the `token_file` (`token.json` by default) and run again to re-authorize. |

**The share-vs-auth same-account trap.** The Google account you complete OAuth with and the
account the sheet is shared with must be the **same account**. Authorizing as account A but
sharing the sheet only with account B is the most common silent failure: the run looks like it
succeeds but reads nothing. When in doubt, open the sheet signed in as the account you authorized
and confirm you can see it.
