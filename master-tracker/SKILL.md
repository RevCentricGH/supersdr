---
name: master-tracker
description: Claude Code skill - runs in a terminal with real Python and local credentials, not in Cowork. Pull one or more reps' Apollo dialer calls into per-rep tabs of a Google Sheet, filtered to the dispositions you care about, deduped, and safe to run on a schedule. Trigger when the user wants to sync Apollo calls into a tracking sheet, build a per-rep outbound activity tracker, or says things like "pull my Apollo calls into the sheet", "update the call tracker", "run master-tracker", or "sync the dialer calls". It pulls each configured rep's calls with paged, 429-aware Apollo search, keeps only the configured dispositions, writes rows deduped by call ID and then by date and prospect (keeping the row with a recording when the dialer logs one conversation twice), never overwrites manual columns, and marks a call ingested only after its row is written so a call tagged after the dialer logged it is still picked up on a later run.
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
3. Maps each kept call to a row and dedupes it: the dialer's call ID is the primary
   identity, then (date, lowercased prospect) against the rows already in the sheet. When
   one conversation is logged twice - same prospect, same day, same disposition, one
   entry with a recording and one without - the row with the recording is the one
   written, so a real interaction is never merged away and duplicates never inflate
   counts. Two caveats: the preference decides between entries seen in the same run
   (once a row is in the sheet it is never rewritten, so a recorded twin that only
   appears on a later run cannot fill the blank), and it needs a configured
   `recording_source` (with none, every row resolves blank and the first entry wins).
   Same-day calls with different dispositions are different conversations; the first
   one keeps the row.
4. Appends new rows to the rep's tab, resolving the Recording URL column through the configured
   recording source (Apollo, Trellus, or a manually attached URL) when one resolves. It only
   appends, so the manual columns you added (Notes, Next Step, and so on) are never overwritten.
5. Marks a call ingested only after its row is written. If a write fails, the call is retried
   next run. If a rep tags a call with a kept disposition after the dialer first logged it, the
   next run picks it up. A duplicate whose (date, prospect) row is already settled in the sheet
   is marked too - append-only means it can never be written, so re-fetching it every run would
   be waste.
6. Rebuilds the summary tab as LIVE spreadsheet formulas referencing the rep tabs: an ICP
   breakdown, a rolling weekly meeting trend, conversion rates (per rep and overall), and a
   rep leaderboard. Because the cells are formulas, the summary keeps itself current as rep
   tabs change between runs; a rebuild only refreshes the shape (rep order, discovered ICP
   categories). It never runs when every rep tab reads back empty while the summary has
   content - that is almost always a failed read, not an empty tracker - and a scheduled
   run that hits this guard exits nonzero so monitoring sees it. `--stats-only`, run by
   hand, overrides the guard.

## The summary tab: live formulas, your formatting

After the pull, master-tracker writes one summary tab (default name "Overall Statistics") as
live spreadsheet formulas that reference the rep tabs. The cells are `COUNTIF`, `COUNTA` and
`SUMPRODUCT` formulas, not numbers computed by the script, so the summary updates itself the
moment a rep tab changes - between runs, with the script not even running.

**The script writes values only. Formatting is yours.** Run `python3 run.py --scaffold` once
to bold and freeze the header rows and percent-format the summary's rate columns, then style
anything - colors, borders, widths, conditional formats, chart tabs - however you like, by
hand or with Claude Cowork or ChatGPT. No refresh ever touches formatting, so restyling can
never be undone by the tracker and restyling can never break the tracker. Rates are written
as plain numbers (0 to 1), so they stay chartable and sortable; the percent look comes from
the one-time format, not from the values. What a rebuild does rewrite is the summary grid's cell values, so
keep manual columns and notes off the summary tab; they belong on the rep tabs. Adding your
own extra tabs with your own formulas or charts over the rep tabs is always safe.

A rebuild is only needed when the SHAPE changes: a rep added or renamed, a new ICP category
to discover, changed dispositions or labels. Trigger it with `python3 run.py --stats-only`
(no Apollo pull). It reads each rep tab's actual header row first and builds formulas from
the columns' real positions, so an operator who moved or added columns still gets correct
counts. A rep tab whose header exists but lost its Date or disposition column stops the
rebuild rather than silently counting the wrong one; a rep with no tab yet (added to config
before their first pull) just gets their tab created and shows zeros.

The summary holds:

- **ICP breakdown** - one `COUNTIF` row per category against your ICP column across all rep
  tabs. Set `stats.icp_categories` for a fixed list (stable formulas); leave it unset and
  categories are discovered from the live rows at each rebuild instead.
- **Meeting trends** - a rolling window of `stats.trend_weeks` weeks (default 10), oldest
  first, counting `stats.meeting_dispositions` rows per week. Week boundaries come from
  `TODAY()` in the sheet, so the window slides by itself.
- **Conversion rates** - per rep and overall: conversations (any disposition), qualified
  conversations (`stats.qualified_dispositions`; unset means every conversation counts),
  meetings, meeting rate, and conversion rate. Rates guard the zero-denominator case, and the
  overall row sums the per-rep cells rather than averaging rates, so a low-volume rep cannot
  skew it.
- **Rep leaderboard** - reps ordered by `stats.leaderboard_metric`: `rate`, `meetings`, or
  `calls`. The ordering is frozen at rebuild time (a sheet cannot sort itself); the values
  are live formulas. With the `rate` metric, the value sits in column E so the one-time
  percent format covers it; count metrics sit next to the name in column B.

Tab names, the ICP column and categories, the trend window, the dispositions, the metric, and
every label are config (`stats` block), so nothing about the summary is hardcoded to one team.

## The data contract (the sheet is the interface)

The rep tabs are a stable, documented surface, not private state. Each rep tab is:

```
Date | Prospect | Disposition | Phone | Duration (sec) | Call ID | Recording URL | <your manual columns>
```

One row per call, header in row 1, appended in date order, manual columns never written by
the tool. Anything that can read or write a Google Sheet can work with the tracker through
this contract - no Python runtime needed:

- **Apollo's API or MCP** in an interactive Claude session can look up a call, a rep id, or a
  disposition list, and land rows in the same shape.
- **Trellus's API or MCP** can resolve recording links for rows whose call notes carry a
  session id.
- **Claude Cowork or ChatGPT** can read the rep tabs to build custom views, charts, or a
  restyled summary on their own tabs.

Three rules keep that safe. Never rewrite an existing row (the tracker's dedup and the
operator's manual columns both depend on append-only). Never let an interactive session
write the summary grid (the next rebuild rewrites it). And write disposition and ICP values
exactly - no stray leading or trailing spaces - because the summary's formulas match labels
whitespace-exactly (case does not matter). The scheduled Python pipeline stays
the source of truth for bulk ingestion because it carries the hardening - dedup, backoff,
mark-after-write, the anti-wipe guard - that an ad-hoc session does not.

## Operating lessons (hard-won, inherited from production)

Failure modes observed running trackers like this in production for months. Most are silent:
the run reports success while importing nothing.

- **An empty 200 is not an empty tracker.** Apollo can return HTTP 200 with zero results
  when a key hits its daily quota - the read is lying, not empty. If a pull suddenly returns
  nothing for every rep, suspect the key before trusting the result. A 401 means the key is
  dead; a 429 means wait. The rolling `backfill_days` window recovers everything missed while
  a key was down.
- **Abort loudly; never destroy data on a suspicious read.** Appends are inherently safe;
  anything that clears and rewrites must refuse when its input looks wrong. That is why the
  summary rebuild skips when every rep tab reads back empty while the summary has content,
  and refuses a rep tab whose header lost its Date or disposition column.
- **Write values, never formatting.** The recurring path uses value updates only; formats,
  colors, widths and dropdowns belong to the human. Format-touching calls live only in the
  one-time `--scaffold` step.
- **One tracker per Apollo key.** Two trackers sharing a key double-pull and burn the daily
  quota. If you run several configs on one machine, stagger their cron minutes.
- **Diagnose from the run output, not a wrapper's log tail.** When the tracker looks stale,
  run `python3 run.py` by hand and read what it prints - and confirm the cron entry still
  exists. Scheduled jobs have silently fallen out of crontabs and gone unnoticed for weeks.

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
   - `google_sheet_id` - the ID from the sheet URL (`.../spreadsheets/d/<THIS>/edit`). Create a
     blank Google Sheet first if you don't have one and copy the ID from its URL.
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
       most teams dial in Apollo.
     - `trellus` - parse the Trellus session id (a `sess_` token) out of the call note and build
       the recording link. Optional `base_url` overrides the Trellus recording-URL base.
     - `manual-url` - use a recording URL you attach per call by hand. Optional `field` overrides
       the call key the URL is read from (default `manual_recording_url`).
     An unknown `type` fails fast at startup with a clear error; a source that cannot resolve a
     given call leaves that row's column blank without stopping the run.
   - `stats` - the summary tab. `summary_tab` is its tab name; `icp_column` is which manual
     column holds the ICP category; `icp_categories` is an optional fixed category list (unset
     means categories are discovered from the live rows at each rebuild); `trend_weeks` is the
     rolling trend window (default 10); `meeting_dispositions` are the dispositions counted as
     a booked meeting; `qualified_dispositions` are the dispositions counted as a qualified
     conversation (the denominator of the conversion rate; unset means every conversation
     counts); `leaderboard_metric` is `rate`, `meetings`, or `calls`; `labels` are every section
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
python3 run.py --scaffold           # one-time: bold + freeze headers, then formatting is yours
```

It prints how many new rows each rep tab got. Run it again any time, or wire it into cron for an
unattended sync. Re-running is idempotent.

## How it is built

The logic lives in the `mastertracker` package and is unit-tested:

- `disposition_filter.py` - `DispositionFilter`: pure keep-set + prefix match.
- `call_row_mapper.py` - `CallRowMapper`: normalized call record to a sheet row.
- `deduper.py` - `Deduper`: dedup by call ID, then (date, lowercased prospect), preferring
  the row with a recording on a same-day, same-disposition collision.
- `ingest_state.py` - `IngestState`: the ingested-call ledger, marked only after a write.
- `recording_source.py` - `RecordingSource`: pluggable `resolve(call)` with `apollo`, `trellus`,
  and `manual-url` adapters selected by config; the single authority for the Recording URL column.
- `pipeline.py` - wires the above and routes each rep's calls to its tab.
- `stats_builder.py` - `StatsBuilder`: pure assembly of the summary grid as live formulas
  (ICP breakdown, rolling trends, conversion rates, leaderboard) from each rep tab's real
  column positions; live-read rows only order the sections. `rebuild_summary` reads headers
  and rows, applies the anti-wipe guard, clears values, and writes.

The side-effecting wrappers are kept thin and validated by the manual end-to-end run:

- `apollo_client.py` - `ApolloClient`: paged search with 429 backoff.
- `sheet_writer.py` - `SheetWriter`: append-only merge that preserves manual columns.

Run the tests from the repo root:

```
python3 -m pytest master-tracker
```

## Troubleshooting

| Symptom | Likely cause and fix |
| --- | --- |
| Run finishes but no new rows appear | The calls were filtered out or never matched a rep. Check three things: `keep_dispositions` / `keep_prefixes` actually match the disposition labels on the calls (they are case-insensitive but must otherwise match); `backfill_days` reaches back far enough to cover the calls; and each rep's `apollo_user_id` is correct (a wrong id silently returns zero calls). |
| Auth fails or asks to re-authorize every run | The OAuth token expired or was revoked. Delete the `token_file` (`token.json` by default) and run again. The first run reopens the browser and writes a fresh token. |
| Run reports rows written but the sheet looks unchanged | You are pointed at the wrong sheet, or the authorized account cannot see it. Confirm `google_sheet_id` is the id from the sheet URL (`.../spreadsheets/d/<THIS>/edit`), and confirm the sheet is shared with the Google account you authorized. |
| Recording URL column is blank | The recording source is unset or cannot resolve a link for those calls. Confirm the `recording_source` block is present and `type` is one of `apollo`, `trellus`, or `manual-url`. The source is the sole authority for that column, so with no source configured (or `type` left `""`) the column stays blank by design. A configured source still leaves a given row blank if it cannot resolve that one call. |

**The share-vs-auth same-account trap.** The Google account you complete OAuth with (the one the
browser prompts you to pick on first run) and the account the sheet is shared with must be the
**same account**. Authorizing as account A but sharing the sheet only with account B is the most
common silent failure: the run looks like it succeeds but writes nothing you can see, or fails
with a permission error. When in doubt, open the sheet while signed in as the account you
authorized and confirm you have edit access.
