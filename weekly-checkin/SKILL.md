---
name: weekly-checkin
description: Claude Code skill - runs in a terminal with real Python and local credentials, not in Cowork. Build a weekly client-delivery digest for one ISO week and deliver it to a configured destination - a Google Doc, Slack, or email. It reads each client's call and disposition rows from the master-tracker Google Sheet and pulls their SmartLead campaign stats, then assembles a per-client section with the call count, disposition breakdown, and SmartLead sent, open rate, reply rate, and bounce count. Trigger when the user wants a weekly client check-in, or wants to schedule or send the weekly digest - "run weekly-checkin", "send the weekly client report", "schedule the weekly check-in", "how did each client do this week". Runs on a weekly cron or on demand for one ISO week (YYYY-WNN, Monday-anchored); destination and schedule are config, not hardcoded; use --dry-run to preview without sending. It only reads the sheet, never writes to it. Per-student credentials (SmartLead API key and Google OAuth); nothing is hardcoded.
---

# weekly-checkin

> **Claude Code skill - runs in a terminal, NOT Cowork.** This skill is real Python that needs
> a shell, the filesystem, a local SmartLead API key, and a Google OAuth token file. Do not
> upload it into the Cowork desktop app. Run it from a terminal with `python3 run.py --week ...`.

Build a weekly client-delivery digest. For a given ISO week, it reads the call and disposition
rows master-tracker wrote to your Google Sheet and pulls each client's SmartLead campaign stats,
then builds one section per client: how many calls, the disposition breakdown, and the SmartLead
sent count, open rate, reply rate, and bounce count for that week. It delivers the assembled
digest to the destination you set in config (a Google Doc, a Slack channel, or email). Run it on
a weekly cron or on demand.

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
   and delivers the digest to the destination in `config.json` (`delivery.type`: a Google Doc,
   Slack, or email). With `--dry-run` it prints the digest and sends nothing. A week with no
   calls and no campaign stats is skipped, not delivered as an empty section.

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
   - `delivery` - where the digest is sent. See the [Delivery](#delivery) section for the per-type
     fields. `delivery.type` is `google_doc`, `slack`, or `email`.
   - `schedule.cron` - a reference value for your crontab (see [Scheduling](#scheduling-cron)).
     `run.py` does not read it.

3. **Set up Google OAuth.** In Google Cloud Console, enable the Google Sheets API, create an
   OAuth client (Desktop app), download the client secret JSON, and point `credentials_file` at
   it. The first run opens a browser to authorize and writes `token_file` for later runs. The
   skill requests read-only Sheets access.

4. **Share the sheet** with the Google account you authorize.

## Run

```
python3 run.py --week 2026-W22                       # build and deliver, using ./config.json
python3 run.py --week 2026-W22 --config /path/to/config.json
python3 run.py --week 2026-W22 --dry-run             # print the digest, deliver nothing
```

Pass the ISO week you want. On a normal run it builds the digest and delivers it to the
destination in `config.json`. **Run `--dry-run` first** before any live send: it prints the digest
to stdout and skips all delivery, so you can confirm the content and config without messaging a
client or appending to a Doc.

## Delivery

Set one destination in the `delivery` block of `config.json`. `delivery.type` is one of
`google_doc`, `slack`, or `email`. Only the fields for your chosen type are required; the others
in the template are reference placeholders and are ignored. Misconfiguration fails fast with a
single human-readable line (no traceback) naming the missing field or unset variable.

Secrets never live in `config.json`. The Slack webhook URL and the SMTP password are read from
environment variables you name in config, so nothing sensitive is committed or printed.

| `delivery.type` | Required fields | Notes |
| --- | --- | --- |
| `google_doc` | `target` (the Doc ID) | Appends a section to the Doc under a unique `run_id` heading. The OAuth token gains Docs write scope; you re-authorize the first time you use this type. |
| `slack` | `slack_webhook_env` (name of the env var holding the incoming-webhook URL) | POSTs the digest to the webhook. Set the env var before running: `export WEEKLY_CHECKIN_SLACK_WEBHOOK=https://hooks.slack.com/...`. |
| `email` | `target` (recipient), `from_address`, `smtp_host`, `smtp_port`, `smtp_user`, `smtp_password_env` | Sends over SMTP with STARTTLS. `subject` is optional. Set the password env var: `export WEEKLY_CHECKIN_SMTP_PASSWORD=...`. Gmail SMTP (`smtp.gmail.com:587`) with an app password is recommended over a local relay, which strict DMARC domains may mark as spam. |

**Idempotency and retries.** Only Google Doc delivery is reversible: each append carries a unique
`run_id` heading (for example `=== weekly-checkin 2026-06-06T09:00:00-a3f2 ===`), so you can
delete a section by its marker, and two runs in one day produce two independently removable
sections. Slack and email are **not** idempotent: a re-run sends a second message. Treat any
re-run for those backends as a deliberate second send, and dry-run first.

A config-path-namespaced lockfile in your temp dir (`weekly-checkin-<hash>.lock`) prevents two
concurrent runs from both delivering. A lock left by a crashed run is reclaimed automatically (the
holder PID is probed, and a lock older than six hours is treated as stale), so a crash never blocks
future runs permanently.

## Scheduling (cron)

`run.py` does not schedule itself; it runs once per invocation. Put it on a weekly cron. The
`schedule.cron` value in `config.json` is a reference for your own records (the default
`0 9 * * 1` is Monday 9 AM); `run.py` does not read or evaluate it.

Add a crontab entry with **absolute paths** for the interpreter, the script, and the config, since
cron runs with a bare environment and a different working directory. Set any delivery secret env
var in the entry too:

```
# Monday 9 AM: build last week's digest and deliver it. Pass the week explicitly (see below).
0 9 * * 1 cd /abs/path/to/weekly-checkin && WEEKLY_CHECKIN_SLACK_WEBHOOK='https://hooks.slack.com/...' /abs/path/to/python3 run.py --week "$(date -d 'last monday' +\%G-W\%V)" --config /abs/path/to/weekly-checkin/config.json >> /abs/path/to/weekly-checkin/cron.log 2>&1
```

The `$(date ... +\%G-W\%V)` snippet computes the ISO week string; the `%` signs are escaped for
crontab. On macOS `date` lacks `-d`; use `gdate` (coreutils) or pass the week another way. Check
`cron.log` after the first scheduled run to confirm delivery.

## How it is built

The logic lives in the `weeklycheckin` package and is unit-tested:

- `week_filter.py` - `week_bounds`: turns `YYYY-WNN` into a Monday..Sunday `date` pair.
- `config.py` - `load_config` / `validate_config`: fail-fast config validation and cross-client
  `rep_tab` / `smartlead_campaign_id` uniqueness.
- `sheet_reader.py` - `SheetReader`: reads a rep tab's rows for the week from an injected Sheets
  service; strips header whitespace; fails fast on a missing tab, a missing `Date`/`Disposition`
  column, or an unparseable date.
- `digest_builder.py` - `DigestBuilder`: joins the sheet rows and the SmartLead stats into one
  section per client; `render_digest` formats the sections; `digest_has_activity` is the
  empty-week guard that tells `run.py` to skip delivery.
- `deliver.py` - `deliver`: the single join point that validates the `delivery` config and routes
  to one of `deliver_to_doc` / `deliver_to_slack` / `deliver_to_email`. The side-effecting pieces
  (the Docs append, the HTTP POST, the SMTP send) are injected, so the routing, the `run_id`
  heading, the env-var indirection, and the bounded error messages are all unit-tested with fakes.
- `lockfile.py` - the config-path-namespaced lock with atomic acquisition and stale-lock reclaim.

The side-effecting wrappers are kept thin and validated by the manual end-to-end run:

- `smartlead_client.py` - `SmartLeadClient`: per-campaign stats with 429-aware backoff, a
  30-second per-request timeout, and a closed-default date-range check (see below).
- `run.py` - wires the Google OAuth flow, the live Sheets/Docs/Slack/SMTP clients, the lockfile,
  and the `run_id`, then builds and delivers the digest.

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
| Auth fails or asks to re-authorize every run | The OAuth token expired or was revoked. Delete the `token_file` (`token.json` by default) and run again to re-authorize. Switching `delivery.type` to/from `google_doc` also changes the requested scopes and forces one re-authorization. |
| `weekly-checkin delivery: ...` then exit | Delivery config is wrong: an unsupported `delivery.type`, a missing required field, or an unset/empty secret env var. The message names the exact problem. Fix `config.json` or `export` the env var, then re-run. |
| `Slack webhook returned HTTP 403/404` | The incoming webhook was rotated or revoked. Recreate it in Slack and update the env var named by `slack_webhook_env`. |
| `skipping delivery (nothing to send)` | No calls and no campaign stats for that week. Confirm master-tracker synced the week and the SmartLead campaigns had activity; a genuinely quiet week is skipped by design. |
| `another weekly-checkin run holds ...` | A previous run is still going, or it crashed and left a lock younger than six hours. If the process is gone, delete the named lockfile and re-run; older locks are reclaimed automatically. |

**The share-vs-auth same-account trap.** The Google account you complete OAuth with and the
account the sheet is shared with must be the **same account**. Authorizing as account A but
sharing the sheet only with account B is the most common silent failure: the run looks like it
succeeds but reads nothing. When in doubt, open the sheet signed in as the account you authorized
and confirm you can see it.
