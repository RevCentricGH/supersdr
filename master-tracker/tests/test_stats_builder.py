"""StatsBuilder: rebuild the Overall Statistics summary tab from the live rep tabs.

Covers the validation contract for issue #8:
  - ICP breakdown (1, 2), meeting trends (3, 4), leaderboard (5, 6)
  - reads from live rep tabs (7, 8, 9)
  - clears stale content / idempotent (10, 11)
  - config-driven tab names (12, 13, 14) and labels (15, 16)
"""
import pytest

from mastertracker.stats_builder import StatsBuilder, rebuild_summary
from tests.fakes import FakeSheet

REP_HEADER = ["Date", "Prospect", "Disposition", "ICP"]


def _seed(sheet, tab, *triples):
    """Seed a rep tab with rows; each triple is (disposition, icp, date)."""
    for i, (disp, icp, date) in enumerate(triples):
        sheet.seed_row(
            tab,
            REP_HEADER,
            {"Date": date, "Prospect": f"{tab} P{i}", "Disposition": disp, "ICP": icp},
        )


def _config(reps, **stats_overrides):
    stats = dict(
        summary_tab="Overall Statistics",
        icp_column="ICP",
        meeting_dispositions=["Meeting Booked"],
        leaderboard_metric="calls",
    )
    stats.update(stats_overrides)
    return {"reps": {name: {} for name in reps}, "stats": stats}


def _rows(*dispositions_with_icp):
    """Build rep-tab rows. Each arg is (disposition, icp, date)."""
    out = []
    for i, (disp, icp, date) in enumerate(dispositions_with_icp):
        out.append(
            {
                "Date": date,
                "Prospect": f"Prospect {i}",
                "Disposition": disp,
                "ICP": icp,
            }
        )
    return out


def _builder(**overrides):
    kw = dict(
        icp_column="ICP",
        meeting_dispositions=["Meeting Booked"],
        leaderboard_metric="calls",
        labels=None,
    )
    kw.update(overrides)
    return StatsBuilder(**kw)


def test_icp_breakdown_counts_each_category_across_all_rep_tabs():
    # contract 1, 2
    rep_rows = {
        "Rep A": _rows(
            ("Interested", "SaaS", "2026-05-20"),
            ("Meeting Booked", "SaaS", "2026-05-21"),
            ("Interested", "Agency", "2026-05-22"),
        ),
        "Rep B": _rows(
            ("Interested", "SaaS", "2026-05-20"),
            ("Not Interested", "", "2026-05-21"),
        ),
    }
    breakdown = _builder().icp_breakdown(rep_rows)
    # SaaS appears 3x, Agency 1x; blank ICP is not a category
    assert breakdown == [("SaaS", 3), ("Agency", 1)]


def test_meeting_trends_bucket_meetings_by_week_across_multiple_weeks():
    # contract 3, 4 - only meeting-disposition rows count, grouped into separate week buckets
    rep_rows = {
        "Rep A": _rows(
            ("Meeting Booked", "SaaS", "2026-05-18"),  # ISO week 2026-W21 (Mon)
            ("Meeting Booked", "SaaS", "2026-05-20"),  # same week 2026-W21
            ("Interested", "SaaS", "2026-05-21"),      # not a meeting, ignored
            ("Meeting Booked", "SaaS", "2026-05-26"),  # next week 2026-W22
        ),
        "Rep B": _rows(
            ("Meeting Booked", "Agency", "2026-05-25"),  # 2026-W22
        ),
    }
    trends = _builder().meeting_trends(rep_rows)
    # two distinct week buckets, sorted, each the count of meetings in that week
    assert trends == [("2026-W21", 2), ("2026-W22", 2)]


def test_leaderboard_ranks_reps_by_call_count_descending():
    # contract 5, 6 - "calls" metric is the row count per rep, ranked high to low
    rep_rows = {
        "Rep A": _rows(
            ("Interested", "SaaS", "2026-05-20"),
            ("Meeting Booked", "SaaS", "2026-05-21"),
        ),
        "Rep B": _rows(
            ("Interested", "SaaS", "2026-05-20"),
            ("Interested", "SaaS", "2026-05-21"),
            ("Meeting Booked", "Agency", "2026-05-22"),
        ),
    }
    board = _builder(leaderboard_metric="calls").leaderboard(rep_rows)
    assert board == [("Rep B", 3), ("Rep A", 2)]


def test_leaderboard_can_rank_by_meeting_count():
    # contract 5 - the activity metric is configurable; "meetings" counts meeting rows
    rep_rows = {
        "Rep A": _rows(
            ("Meeting Booked", "SaaS", "2026-05-20"),
            ("Meeting Booked", "SaaS", "2026-05-21"),
            ("Interested", "SaaS", "2026-05-22"),
        ),
        "Rep B": _rows(
            ("Meeting Booked", "Agency", "2026-05-20"),
            ("Interested", "Agency", "2026-05-21"),
        ),
    }
    board = _builder(leaderboard_metric="meetings").leaderboard(rep_rows)
    assert board == [("Rep A", 2), ("Rep B", 1)]


def test_build_grid_uses_configured_labels_for_every_section():
    # contract 15, 16 - section/column headers come from config, so changing them changes output
    labels = {
        "icp_header": "Ideal Customer Profile",
        "icp_category_col": "Segment",
        "icp_count_col": "Calls",
        "trends_header": "Weekly Meetings",
        "trends_week_col": "ISO Week",
        "trends_count_col": "Booked",
        "leaderboard_header": "Top Performers",
        "leaderboard_rep_col": "Teammate",
        "leaderboard_metric_col": "Total Calls",
    }
    rep_rows = {
        "Rep A": _rows(
            ("Meeting Booked", "SaaS", "2026-05-20"),
            ("Interested", "SaaS", "2026-05-21"),
        ),
    }
    grid = _builder(labels=labels).build_grid(rep_rows)
    flat = [cell for row in grid for cell in row]
    for label in labels.values():
        assert label in flat
    # the section header rows appear in ICP -> trends -> leaderboard order
    assert flat.index("Ideal Customer Profile") < flat.index("Weekly Meetings") < flat.index("Top Performers")
    # data rows render alongside their labels
    assert ["SaaS", 2] in grid          # ICP breakdown row
    assert ["2026-W21", 1] in grid      # one booked meeting that week
    assert ["Rep A", 2] in grid         # leaderboard row, 2 calls


def test_from_config_reads_columns_dispositions_metric_and_labels():
    # contract 15, 16 - the stats block drives the builder; no hardcoded values
    config = {
        "stats": {
            "summary_tab": "Overall Statistics",
            "icp_column": "Segment",
            "meeting_dispositions": ["Meeting Booked", "Demo Set"],
            "leaderboard_metric": "meetings",
            "labels": {"icp_header": "Customer Segments"},
        }
    }
    builder = StatsBuilder.from_config(config)
    assert builder.icp_column == "Segment"
    assert builder.meeting_dispositions == {"meeting booked", "demo set"}
    assert builder.leaderboard_metric == "meetings"
    assert builder.labels["icp_header"] == "Customer Segments"
    # unspecified labels fall back to generic defaults
    assert builder.labels["leaderboard_header"] == "Rep Leaderboard"


def test_rebuild_summary_reads_every_rep_tab_and_writes_correct_sections():
    # contract 7, 9, and end-to-end correctness of 1-6
    sheet = FakeSheet()
    _seed(sheet, "Rep A",
          ("Meeting Booked", "SaaS", "2026-05-18"),
          ("Interested", "SaaS", "2026-05-20"))
    _seed(sheet, "Rep B",
          ("Meeting Booked", "Agency", "2026-05-25"),
          ("Meeting Booked", "SaaS", "2026-05-26"),
          ("Interested", "Agency", "2026-05-27"))
    config = _config(["Rep A", "Rep B"])

    rebuild_summary(config, sheet=sheet)
    grid = sheet.grid("Overall Statistics")

    # ICP breakdown: SaaS 3, Agency 2
    assert ["SaaS", 3] in grid
    assert ["Agency", 2] in grid
    # meeting trends: 1 in 2026-W21, 2 in 2026-W22
    assert ["2026-W21", 1] in grid
    assert ["2026-W22", 2] in grid
    # leaderboard by calls: Rep B (3) ahead of Rep A (2) - both rep tabs were read
    assert ["Rep B", 3] in grid
    assert ["Rep A", 2] in grid


def test_rebuild_summary_includes_a_rep_tab_with_no_rows():
    # contract 9 - a configured rep with an empty tab still appears, never silently skipped
    sheet = FakeSheet()
    _seed(sheet, "Rep A", ("Interested", "SaaS", "2026-05-20"))
    sheet.ensure_header("Rep B", REP_HEADER)  # exists but empty
    config = _config(["Rep A", "Rep B"])

    rebuild_summary(config, sheet=sheet)
    grid = sheet.grid("Overall Statistics")
    assert ["Rep A", 1] in grid
    assert ["Rep B", 0] in grid


def test_rebuild_summary_clears_the_summary_tab_before_writing():
    # contract 10 - stale rows from a prior, larger run do not survive
    sheet = FakeSheet()
    _seed(sheet, "Rep A", ("Interested", "SaaS", "2026-05-20"))
    config = _config(["Rep A"])
    # prior run left a long grid with a stale trailing row
    sheet.write_grid("Overall Statistics", [["stale"]] * 40)

    rebuild_summary(config, sheet=sheet)
    grid = sheet.grid("Overall Statistics")
    assert "Overall Statistics" in sheet.cleared
    assert ["stale"] not in grid


def test_rebuild_summary_is_idempotent():
    # contract 11 - two runs in a row produce identical summary output
    sheet = FakeSheet()
    _seed(sheet, "Rep A",
          ("Meeting Booked", "SaaS", "2026-05-18"),
          ("Interested", "Agency", "2026-05-26"))
    config = _config(["Rep A"])

    rebuild_summary(config, sheet=sheet)
    first = [list(r) for r in sheet.grid("Overall Statistics")]
    rebuild_summary(config, sheet=sheet)
    second = [list(r) for r in sheet.grid("Overall Statistics")]
    assert first == second


def test_rebuild_summary_reflects_a_new_row_on_the_next_run():
    # contract 8 - adding a meeting row to a live rep tab changes the next summary
    sheet = FakeSheet()
    _seed(sheet, "Rep A", ("Meeting Booked", "SaaS", "2026-05-18"))
    config = _config(["Rep A"])

    rebuild_summary(config, sheet=sheet)
    assert ["2026-W21", 1] in sheet.grid("Overall Statistics")

    _seed(sheet, "Rep A", ("Meeting Booked", "SaaS", "2026-05-19"))  # same week
    rebuild_summary(config, sheet=sheet)
    assert ["2026-W21", 2] in sheet.grid("Overall Statistics")


def test_rebuild_summary_uses_configured_tab_names():
    # contract 12, 13, 14 - rename the summary tab and a rep tab in config only
    sheet = FakeSheet()
    _seed(sheet, "SDR One", ("Meeting Booked", "SaaS", "2026-05-18"))
    config = _config(["SDR One"], summary_tab="Team Stats")

    rebuild_summary(config, sheet=sheet)
    # written to the configured summary tab name, read from the configured rep tab name
    assert sheet.grid("Team Stats")
    assert ["SDR One", 1] in sheet.grid("Team Stats")
    assert sheet.grid("Overall Statistics") == []


def test_is_meeting_uses_the_configured_disposition_column():
    # a sheet whose disposition column is named differently still counts meetings, instead of
    # silently yielding zero from a hardcoded "Disposition" key
    builder = _builder(disposition_column="Outcome")
    rep_rows = {
        "Rep A": [
            {"Date": "2026-05-18", "Outcome": "Meeting Booked", "ICP": "SaaS"},
            {"Date": "2026-05-19", "Outcome": "Interested", "ICP": "SaaS"},
        ]
    }
    assert builder.meeting_trends(rep_rows) == [("2026-W21", 1)]


def test_unknown_leaderboard_metric_is_rejected():
    # a config typo ("meeting") raises instead of silently falling back to call counts
    with pytest.raises(ValueError):
        _builder(leaderboard_metric="meeting")


def test_rebuild_summary_errors_clearly_when_stats_block_is_missing():
    # documented precondition: no stats block -> a clear ValueError, not a bare KeyError
    sheet = FakeSheet()
    with pytest.raises(ValueError):
        rebuild_summary({"reps": {"Rep A": {}}}, sheet=sheet)
