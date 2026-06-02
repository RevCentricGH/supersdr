---
name: master-tracker
description: Pull one or more reps' Apollo dialer calls into per-rep tabs of a Google Sheet, filtered to the dispositions you care about, deduped, and safe to run on a schedule. Trigger when the user wants to sync Apollo calls into a tracking sheet, build a per-rep outbound activity tracker, or says things like "pull my Apollo calls into the sheet", "update the call tracker", "run master-tracker", or "sync the dialer calls". This is a Claude Code skill that runs in a terminal with real Python and local credentials, not a Cowork skill. It pulls each configured rep's calls with paged, 429-aware Apollo search, keeps only the configured dispositions, writes rows deduped by date and prospect, never overwrites manual columns, and marks a call ingested only after its row is written so a call tagged after the dialer logged it is still picked up on a later run.
---

# master-tracker

> **Claude Code skill - runs in a terminal, NOT Cowork.** This skill is real Python that needs
> a shell, the filesystem, local API keys, and a Google OAuth token file. Do not upload it into
> the Cowork desktop app. Run it from a terminal (or a cron job) with `python3 run.py`.

Pull each rep's dialed Apollo calls into per-rep tabs of a Google Sheet. The sheet becomes the
single source of truth for outbound activity: one tab per rep, one row per call, filtered to the
dispositions you care about. It is safe to run repeatedly. Re-runs never duplicate rows and never
touch the columns you fill in by hand.

## What it does on each run

For every rep in your config:

1. Searches that rep's Apollo phone calls, paged, backing off on HTTP 429, bounded to the
   backfill window.
2. Keeps only calls whose disposition is in your keep list or starts with a keep prefix. Every
   other call is skipped before any per-call work, so a skipped call costs nothing and is
   re-evaluated on the next run.
3. Maps each kept call to a row and dedupes by (date, lowercased prospect) against the rows
   already in the sheet, so no duplicates.
4. Appends new rows to the rep's tab, resolving the Recording URL column through the configured
   recording source (Apollo, Trellus, or a manually attached URL) when one resolves. It only
   appends, so the manual columns you added (Notes, Next Step, and so on) are never overwritten.
5. Marks a call ingested only after its row is written. If a write fails, the call is retried
   next run. If a rep tags a call with a kept disposition after the dialer first logged it, the
   next run picks it up.
6. Rebuilds the summary tab from the live rep tabs: an ICP breakdown (counts per ICP category),
   meeting trends (booked meetings bucketed by week), and a rep leaderboard (reps ranked by
   activity). The summary tab is cleared and rewritten each run, so it is always current and
   safe to re-run.

## The summary tab

After the pull, master-tracker rebuilds one summary tab (default name "Overall Statistics")
straight from the rows in the live rep tabs. It owns that tab and rewrites it wholesale, so it
never duplicates and never goes stale:

- **ICP breakdown** - counts the rows in each rep tab by the value in your ICP column, totaled
  across all reps. Fill in the `ICP` column (a manual column) per row to categorize a prospect.
- **Meeting trends** - rows whose disposition is in `stats.meeting_dispositions`, bucketed by
  ISO week, so you can see booked meetings rising or falling week over week.
- **Rep leaderboard** - reps ranked by `stats.leaderboard_metric`: `calls` (all tracked rows)
  or `meetings` (meeting-disposition rows).

Tab names, the ICP column, the meeting dispositions, the metric, and every label are config
(`stats` block), so nothing about the summary is hardcoded to one team. Rebuild it without
re-pulling Apollo with `python3 run.py --stats-only`.

## Setup

This is a one-time setup per operator. Everything runs on your own accounts.

1. **Install dependencies** (Python 3.10+):

   ```
   cd master-tracker
   python3 -m pip install -r requirements.txt
   ```

2. **Create your config.** Copy the template and fill it in. Your real config is gitignored.

   ```
   cp config.template.json config.json
   ```

   Fields:
   - `apollo_api_key` - your Apollo API key (Settings -> Integrations -> API in Apollo).
   - `google_sheet_id` - the ID from the sheet URL (`.../spreadsheets/d/<THIS>/edit`).
   - `reps` - a map of `"Rep display name": { "apollo_user_id": "<id>" }`. The display name is
     the tab name. Find a rep's Apollo user id in their Apollo profile URL or via the API. One
     rep is fine; the map just has one entry.
   - `keep_dispositions` - exact disposition labels to keep (case-insensitive).
   - `keep_prefixes` - disposition prefixes to keep, for families like `Callback - next week`.
   - `backfill_days` - how many days back to pull on each run.
   - `manual_columns` - columns you maintain by hand. Reserved on every row and never written to.
     Includes `ICP` by default, the column the summary tab's ICP breakdown counts.
   - `recording_source` - which dialer the Recording URL column is resolved from. `type` is one
     of `apollo`, `trellus`, or `manual-url`. Remove the whole block (or set `type` to `""`) to
     leave the column blank. The recording source is the sole authority for that column, so a
     call's recording link only shows up once a source is configured and resolves one.
     - `apollo` - use the recording URL Apollo's API attaches to each call. This is the default;
       students dial in Apollo.
     - `trellus` - parse the Trellus session id (a `sess_` token) out of the call note and build
       the recording link. Optional `base_url` overrides the Trellus recording-URL base.
     - `manual-url` - use a recording URL you attach per call by hand. Optional `field` overrides
       the call key the URL is read from (default `manual_recording_url`).
     An unknown `type` fails fast at startup with a clear error; a source that cannot resolve a
     given call leaves that row's column blank without stopping the run.
   - `stats` - the summary tab. `summary_tab` is its tab name; `icp_column` is which manual
     column holds the ICP category; `meeting_dispositions` are the dispositions counted as a
     booked meeting; `leaderboard_metric` is `calls` or `meetings`; `labels` are every section
     and column header in the summary. Change any of these without touching code.
   - `google_oauth.credentials_file` / `google_oauth.token_file` - paths to your Google OAuth
     client secret and the token file the skill writes after the first authorization.
   - `state_file` - where the ingested-call ledger is kept.

3. **Set up Google OAuth.** In Google Cloud Console, enable the Google Sheets API, create an
   OAuth client (Desktop app), download the client secret JSON, and point `credentials_file` at
   it. The first run opens a browser to authorize and writes `token_file` for later runs.

4. **Share the sheet** with the Google account you authorize.

## Run

```
python3 run.py                      # uses ./config.json
python3 run.py --config /path/to/config.json
python3 run.py --stats-only         # rebuild the summary tab only, no Apollo pull
```

It prints how many new rows each rep tab got. Run it again any time, or wire it into cron for an
unattended sync. Re-running is idempotent.

## How it is built

The logic lives in the `mastertracker` package and is unit-tested:

- `disposition_filter.py` - `DispositionFilter`: pure keep-set + prefix match.
- `call_row_mapper.py` - `CallRowMapper`: normalized call record to a sheet row.
- `deduper.py` - `Deduper`: dedup by (date, lowercased prospect).
- `ingest_state.py` - `IngestState`: the ingested-call ledger, marked only after a write.
- `recording_source.py` - `RecordingSource`: pluggable `resolve(call)` with `apollo`, `trellus`,
  and `manual-url` adapters selected by config; the single authority for the Recording URL column.
- `pipeline.py` - wires the above and routes each rep's calls to its tab.
- `stats_builder.py` - `StatsBuilder`: pure aggregation of the live rep tabs into the summary
  tab (ICP breakdown, meeting trends, leaderboard); `rebuild_summary` reads, clears, and writes.

The side-effecting wrappers are kept thin and validated by the manual end-to-end run:

- `apollo_client.py` - `ApolloClient`: paged search with 429 backoff.
- `sheet_writer.py` - `SheetWriter`: append-only merge that preserves manual columns.

Run the tests from the repo root:

```
python3 -m pytest master-tracker
```
