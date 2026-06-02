# Handoff - issue #8 (master-tracker: Overall Statistics summary tab)

## 1. What shipped

`StatsBuilder` for `master-tracker`: rebuilds the Overall Statistics summary tab straight from
the live rep tabs, on every run, idempotently.

- **ICP breakdown** - counts rows per distinct value in the configured ICP column, totaled
  across all rep tabs (blank ICP is not a category), sorted by count then name.
- **Meeting trends** - rows whose disposition is in `stats.meeting_dispositions`, bucketed by
  ISO year-week (`YYYY-Www`), sorted chronologically; multi-week by construction.
- **Rep leaderboard** - every configured rep ranked by `stats.leaderboard_metric`: `calls`
  (all tracked rows) or `meetings` (meeting-disposition rows), descending, name tie-break.
- `rebuild_summary(config, *, sheet)` reads each configured rep tab live, builds the grid,
  **clears the summary tab, then writes** - so stale rows never persist and two runs are
  identical. Wired into `run.py` after the Apollo pull, plus `python3 run.py --stats-only`.
- Tab names, the ICP column, meeting dispositions, the metric, and every section/column label
  are config (`stats` block); generic English fallbacks for labels, nothing RevCentric-specific.
- 12 new pytest tests in `master-tracker/tests/test_stats_builder.py` (full suite: 85 passed).
- Manual end-to-end validated against a populated stubbed sheet; recorded in DEV_STATUS.md with
  the operator checklist for a live-sheet confirmation.

## 2. Public interface exported

In the existing `mastertracker` package (folder `master-tracker/`):

- `mastertracker.stats_builder.StatsBuilder(*, icp_column, meeting_dispositions,
  leaderboard_metric="calls", labels=None)` with pure methods:
  - `.icp_breakdown(rep_rows) -> [(category, count)]`
  - `.meeting_trends(rep_rows) -> [(iso_week, count)]`
  - `.leaderboard(rep_rows) -> [(rep_name, value)]`
  - `.build_grid(rep_rows) -> list[list]` (the full 2D summary block)
  - classmethod `.from_config(config) -> StatsBuilder`
  - module constant `DEFAULT_LABELS` (nine generic label keys).
  `rep_rows` is `{rep_name: [row_dict, ...]}`; a row_dict is header-keyed (the rep-tab columns).
- `mastertracker.stats_builder.rebuild_summary(config, *, sheet, builder=None) -> grid`.
  Reads `config["reps"]` keys as the rep tab names, writes `config["stats"]["summary_tab"]`.
- `SheetWriter` gained three live-sheet methods (thin, manual-validated like the rest of it):
  `read_rows(tab) -> list[dict]`, `clear_tab(tab)`, `write_grid(tab, values_2d)`.

**Sheet duck-type the orchestrator depends on** (same shape FakeSheet implements):
`read_rows(tab) -> list[dict]`, `clear_tab(tab)`, `write_grid(tab, values_2d)`.

## 3. Files touched

- `master-tracker/mastertracker/stats_builder.py` (new)
- `master-tracker/tests/test_stats_builder.py` (new)
- `master-tracker/mastertracker/sheet_writer.py` (read_rows / clear_tab / write_grid)
- `master-tracker/mastertracker/__init__.py` (doc StatsBuilder)
- `master-tracker/tests/fakes.py` (FakeSheet: read_rows / clear_tab / write_grid / grid; models
  Sheets `values.update`-at-A1 overlay so the clear-before-write behavior is genuinely tested)
- `master-tracker/config.template.json` (`stats` block; `ICP` added to `manual_columns`)
- `master-tracker/run.py` (rebuild summary after the pull; `--stats-only` flag)
- `master-tracker/SKILL.md` (summary-tab section, stats config, module list, run usage)
- `DEV_STATUS.md` (gitignored) - CI gate + dated end-to-end transcript + per-assertion log + checklist
- `.ralph/handoff-8.md` (this file)

## 4. Decisions downstream issues must inherit

- **Literal values, not formulas.** The PRD framed StatsBuilder as "emits Sheets formulas",
  but the contract requires verifiable correct values. StatsBuilder computes aggregations in
  Python and writes literal cells, so correctness is unit-testable and idempotency is exact.
  Any later stats work should keep computing values, not emit live formulas.
- **The summary tab is owned wholesale.** `rebuild_summary` clears the entire summary tab then
  writes the full block. "Sections it owns" = the whole tab; StatsBuilder is its only writer.
  Do not interleave other content into that tab.
- **Rep tab name = the `config["reps"]` key.** This already holds in `pipeline.run` (`tab=rep_name`).
  Stats reads the same keys; keep rep tab naming driven by the reps map, never hardcoded.
- **ICP is a manual column.** The ICP breakdown counts a manual column (`stats.icp_column`,
  default `ICP`) the operator fills in per row. It is in `manual_columns`, so the ingest reserves
  it blank and never overwrites it.
- **Week bucket = ISO year-week `YYYY-Www`** from the `Date` cell. Deterministic and sortable;
  rows with an empty/unparseable date are dropped from trends only.
- **Meeting match is case-insensitive**, consistent with `DispositionFilter`.

## 5. Intentionally out of scope

- Live-SaaS confirmation against a real Google Sheet. No OAuth credentials in the AFK
  environment; the credentialed Sheets boundary is stubbed (FakeSheet), all StatsBuilder logic
  is the genuine path. DEV_STATUS.md has the operator checklist to confirm on a live account.
- Charts, conditional formatting, or styled cells in the summary tab - values only.
- Per-rep stats sections or time-windowed leaderboards (e.g. "this week vs last") - the
  leaderboard is all-time over what is in the rep tabs.
- Sheets formulas referencing rep tabs - rejected in favor of testable literal values (see 4).
- Any new dialer/recording work - unrelated to this slice.
