---
name: master-tracker
description: Claude Code skill - runs in a terminal with real Python and local credentials, not in Cowork. Pull one or more reps' Apollo dialer calls into per-rep tabs of a Google Sheet, filtered to the dispositions you care about, deduped, and safe to run on a schedule. Trigger when the user wants to sync Apollo calls into a tracking sheet, build a per-rep outbound activity tracker, or says things like "pull my Apollo calls into the sheet", "update the call tracker", "run master-tracker", or "sync the dialer calls". It pulls each configured rep's calls with paged, 429-aware Apollo search, keeps only the configured dispositions, writes rows deduped by date and prospect, never overwrites manual columns, and marks a call ingested only after its row is written so a call tagged after the dialer logged it is still picked up on a later run.
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
   meeting trends (booked meetings bucketed by week), conversion rates (meeting rate and
   conversation-to-meeting rate, per rep and overall), and a rep leaderboard ranked by rate.
   The summary tab is cleared and rewritten each run, so it is always current and safe to re-run.

## The summary tab

After the pull, master-tracker rebuilds one summary tab (default name "Overall Statistics")
straight from the rows in the live rep tabs. It owns that tab and rewrites it wholesale, so it
never duplicates and never goes stale. Do not add manual columns or notes to the summary tab -
the rebuild wipes them. Manual columns belong on the rep tabs. The summary holds:

- **ICP breakdown** - counts the rows in each rep tab by the value in your ICP column, totaled
  across all reps. Fill in the `ICP` column (a manual column) per row to categorize a prospect.
- **Meeting trends** - rows whose disposition is in `stats.meeting_dispositions`, bucketed by
  ISO week, so you can see booked meetings rising or falling week over week.
- **Conversion rates** - per rep and overall, computed straight from the dispositions already in
  the rep tabs:
  - *Conversations* - rows with any disposition (a connected call).
  - *Qualified conversations* - rows whose disposition is in `stats.qualified_dispositions`.
  - *Meeting rate* - meetings divided by conversations.
  - *Conversation-to-meeting conversion rate* - meetings divided by qualified conversations.
  Rates show as percentages; a rep with no conversations reads `0.0%` rather than erroring. The
  overall row is summed meetings over summed conversations, not the average of the per-rep rates,
  so a low-volume rep cannot skew it. Leave `qualified_dispositions` unset and every conversation
  counts as qualified, so the conversion rate equals the meeting rate.
- **Rep leaderboard** - reps ranked by `stats.leaderboard_metric`: `rate` (conversion rate, so
  efficiency beats volume; ties break on meeting count), `meetings` (meeting-disposition rows),
  or `calls` (all tracked rows).

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

2. **Create your config.** The shipped `config.template.json` contains pipeline/QM thresholds for other tools — it is NOT the runtime config schema. Create `config.json` from scratch with the fields below, or copy `templates/runtime-config-example.json` (included in this skill) and fill in your values. Your real config is gitignored.

   ```
   cp templates/runtime-config-example.json config.json
   # then edit config.json with your actual values
   ```

   Fields:
   - `apollo_api_key` - your Apollo API key (Settings -> Integrations -> API in Apollo).
   - `google_sheet_id` - the ID from the sheet URL (`.../spreadsheets/d/<THIS>/edit`). Create a
     blank Google Sheet first if you don't have one and copy the ID from its URL.
   - `reps` - a map of `"Rep display name": { "apollo_user_id": "<id>" }`. The display name is
     the tab name. Find a rep's Apollo user id in their Apollo profile URL or via the API. One
     **One rep is fine; the map just has one entry.**
     - **Apollo key sourcing (RevCentric).** Do not look in `config.yaml` or treat this as a generic machine. For RevCentric, the live Apollo keys are in `/Users/kevintran/rc-automations/.env` (`APOLLO_API_KEY_CEKURA`, `_CRUX`, `_MZERO`). Paste the literal value into `config.json`; `run.py` does not resolve env vars. See `references/revcentric-paths.md` for the mapping.
     - **Skill installation path.** The installed skill lives at `~/.hermes/skills/master-tracker/`. There is no profile-based installation at `~/.hermes/profiles/revcentric/skills/master-tracker/` on this machine. Any command or reference to the profile path is stale.
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
     column holds the ICP category; `meeting_dispositions` are the dispositions counted as a
     booked meeting; `qualified_dispositions` are the dispositions counted as a qualified
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
5. **Cron / scheduled runs: pass `--config` with an absolute path.** The default `./config.json`
   is relative to cwd and will not resolve from an unattended job. For a complete path rules
   checklist, see `references/config-setup.md`. A runtime config example (correct schema) is at
   `templates/runtime-config-example.json`; setup diagnostic patterns are in
   `references/setup-diagnostic.md`. Rep user IDs that return zero calls need resolution — see
   `references/apollo-user-id-resolution.md`. Disposition labels require manual mapping since
   Apollo's faceting does not reliably return them — see `references/apollo-disposition-mapping.md`.

## Run

```
python3 run.py                      # uses ./config.json
python3 run.py --config /path/to/config.json
python3 run.py --stats-only         # rebuild the summary tab only, no Apollo pull
```

It prints how many new rows each rep tab got. Run it again any time, or wire it into cron for an
unattended sync. Re-running is idempotent.

## Cron / unattended runs

Always pass `--config` with an absolute path. Cron `cwd` is unpredictable and `./config.json`
will silently fail if the job starts from a different directory:

    python3 /Users/kevintran/.hermes/skills/master-tracker/run.py \
      --config /Users/kevintran/.hermes/skills/master-tracker/config.json

If you see references to an older profile path such as `~/.hermes/profiles/revcentric/skills/master-tracker/`, that directory does not exist on this machine. The active skill lives at `~/.hermes/skills/master-tracker/`. Use that path for both `run.py` and `--config`.

Use `--stats-only` for a summary refresh without hitting Apollo.

### Cron reporting guardrails

For scheduled operational updates, do a fast config-path preflight before treating the cycle as
normal:

1. Confirm the installed skill directory exists.
2. Confirm the absolute `config.json` path exists before running, or run the command and capture the
   exact traceback if it fails at config load.
3. If the config is missing or invalid, report it as an **operational breach** with the exact path
   and the command attempted. Do **not** return `[SILENT]` for setup blockers: silent is only for a
   genuinely healthy cycle with nothing new to report.
4. If the sync cannot run, mark today's numbers and threshold validation as unavailable rather than
   inventing zeros or assuming targets were missed.
5. The one most important action should be the smallest concrete unblocker, usually restoring or
   creating the live config at the absolute path used by cron.

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
  tab (ICP breakdown, meeting trends, conversion rates, rate-ranked leaderboard); `rebuild_summary`
  reads, clears, and writes.

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
| Run aborts before doing anything (config not found) | `config.json` is missing. The script defaults to `./config.json` relative to cwd. Run from the skill directory or pass `--config <absolute-path-to-config.json>`. See `references/config-setup.md` for the full path rules and a checklist. If the failure repeats across multiple cron runs (the most common initial-state failure on this operator's machine), the file was never created after installation. Create it before any unattended run will succeed. |
| Run finishes but no new rows appear | The calls were filtered out or never matched a rep. Check three things: `keep_dispositions` / `keep_prefixes` actually match the disposition labels on the calls (they are case-insensitive but must otherwise match); `backfill_days` reaches back far enough to cover the calls; and each rep's `apollo_user_id` is correct (a wrong id silently returns zero calls). |
| Auth fails or asks to re-authorize every run | The OAuth token expired or was revoked. Delete the `token_file` (`token.json` by default) and run again. The first run reopens the browser and writes a fresh token. |
| Run reports rows written but the sheet looks unchanged | You are pointed at the wrong sheet, or the authorized account cannot see it. Confirm `google_sheet_id` is the id from the sheet URL (`.../spreadsheets/d/<THIS>/edit`), and confirm the sheet is shared with the Google account you authorized. |
| Recording URL column is blank | The recording source is unset or cannot resolve a link for those calls. Confirm the `recording_source` block is present and `type` is one of `apollo`, `trellus`, or `manual-url`. The source is the sole authority for that column, so with no source configured (or `type` left `""`) the column stays blank by design. A configured source still leaves a given row blank if it cannot resolve that one call. |
| Cron preflight searches `~/.hermes/profiles/revcentric/skills/master-tracker/` and finds nothing | The `~/.hermes/profiles/` directory may be empty on this machine. The actual installed skill lives at `~/.hermes/skills/master-tracker/`. When hunting for the skill or config from cron, start there first. Only check a profile path if it actually exists. |
| Rep's configured `apollo_user_id` returns zero calls (silent failure) | A wrong user ID silently produces zero results — no error is raised. Fix: query Apollo without any `user_ids` filter for 1–2 pages, scan the `caller_name` field to find the rep's actual user ID, then update config.json. See `references/apollo-user-id-resolution.md`. |
| Disposition labels in `keep_dispositions` don't match API outcome IDs | Apollo returns phone call outcomes as opaque IDs (`phone_call_outcome_id`). The faceting endpoint does not reliably return human-readable disposition labels in all query contexts (especially with user filters). Outcome IDs must be mapped to labels. See `references/apollo-disposition-mapping.md`. |
| Apollo `/organizations/{id}/people` returns 404 | That endpoint is not available on this Apollo plan. Do not retry. Use Apollo MCP `search_people` with `filters.company_names` and `filters.company_domains` instead. |
| Apollo `search_people` with `company_names` filter returns unrelated people when the target company is small or not fully indexed | On RevCentric searches, Apollo returned unrelated executive records from random companies. This is a known data-quality issue. If the company domain is known, use `company_domains` instead. If neither filter yields the target company's employees, fall back to looking up rep profile URLs directly or ask the operator for the IDs. |
| OAuth token has gmail-only scopes and sheets writes fail | Existing `token.json` files (e.g. `~/.config/gmail/token.json`) were created for gmail scopes only. Deleting and re-running interactively will re-prompt for all scopes configured in `run.py`'s `SCOPES` list (`spreadsheets`). After re-auth, the same `token_file` path is reused. Do not reuse a gmail-scope token for Sheets. |

**Apollo API key location (RevCentric).** Keys are in `/Users/kevintran/rc-automations/.env` under `APOLLO_API_KEY_CEKURA`, `_CRUX`, and `_MZERO`. Paste the literal value into `config.json`; `run.py` does not resolve env vars. Do not chase `config.yaml` first for this skill.

**RevCentric resource paths (current).**

| Resource | Path |
|---|---|
| Skill directory | `/Users/kevintran/.hermes/skills/master-tracker/` |
| Cron script | `/Users/kevintran/.hermes/skills/master-tracker/run.py` |
| Cron `--config` path | `/Users/kevintran/.hermes/skills/master-tracker/config.json` |
| Apollo keys `.env` | `/Users/kevintran/rc-automations/.env` |
| Google OAuth credentials | `/Users/kevintran/.config/gmail/credentials.json` |
| Google OAuth token | `/Users/kevintran/.config/gmail/token.json` |
| Client campaign sheets | `/Users/kevintran/rc-automations/pipeline/clients/*.yaml` |

Do not reference a non-existent profile-path install such as `/Users/kevintran/.hermes/profiles/revcentric/skills/master-tracker/`.

**Rep `apollo_user_id` lookup.** No rep user IDs are stored on disk. Resolve them via the Apollo MCP / People API against org `64c56701db745f008bac103a`, then populate `config.json` `reps`.

**Master-tracker `google_sheet_id`.** Not stored on disk in any known file. Create a blank Google Sheet, extract the ID from its URL, and place it into `config.json`. Client campaign sheet IDs in `rc-automations/pipeline/clients/*.yaml` are unrelated.

**Repeated cron failure pattern.**

1. Does `config.json` exist at `/Users/kevintran/.hermes/skills/master-tracker/config.json`?
2. Is it based on `templates/runtime-config-example.json`, not `config.template.json`?
3. Is `apollo_api_key` populated from `/Users/kevintran/rc-automations/.env`?
4. Does `google_oauth.token_file` exist?
5. Is `google_sheet_id` set?

A missing config blocks all downstream work. Report as operational breach, never `[SILENT]`.

**The share-vs-auth same-account trap.** The Google account you complete OAuth with (the one the
browser prompts you to pick on first run) and the account the sheet is shared with must be the
**same account**. Authorizing as account A but sharing the sheet only with account B is the most
common silent failure: the run looks like it succeeds but writes nothing you can see, or fails
with a permission error. When in doubt, open the sheet while signed in as the account you
authorized and confirm you have edit access.

**Config schema trap.** The shipped `config.template.json` holds pipeline/QM thresholds for other tools. It is **not** the runtime config schema. If you copy it verbatim to `config.json`, the file loads but contains no `apollo_api_key`, `google_sheet_id`, `reps`, or `google_oauth` blocks. Use `templates/runtime-config-example.json` as the basis for `config.json`, not `config.template.json`.

**Cron cwd drift.** Cron does not inherit your shell cwd. If the cron command omits `--config` or passes a relative path, the run dies with `FileNotFoundError: 'config.json'` on an unknown directory. The preflight in `references/config-setup.md` guards against this.

**Apollo auth header format.** Use `X-Api-Key` (not `Bearer`) as the authentication header for Apollo API calls. The key value is pasted directly from `.env`; do not prepend "Bearer " or wrap in quotes. Example: `"X-Api-Key": "4-adDwct70-wSKu3H94QEg"`.
