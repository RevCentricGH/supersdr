"""StatsBuilder: the summary is written as LIVE formulas referencing the rep tabs;
live-read rows only order the sections and discover ICP categories (contract 20, 21, 22)."""
import pytest

from mastertracker.stats_builder import (
    RepLayout,
    StatsBuilder,
    _col_letter,
    _rep_layout,
    rebuild_summary,
)
from tests.fakes import FakeSheet

LAYOUT = RepLayout(date="A", disposition="C", icp="F")


def _builder(**overrides):
    kwargs = dict(
        icp_column="ICP",
        meeting_dispositions=["Meeting Booked"],
        qualified_dispositions=["Interested", "Meeting Booked"],
        leaderboard_metric="rate",
    )
    kwargs.update(overrides)
    return StatsBuilder(**kwargs)


def _row(dispo="Interested", icp="", date="2026-05-20"):
    return {"Date": date, "Disposition": dispo, "ICP": icp}


def _section(grid, header):
    """Rows of one labeled section: from its header row to the next blank row."""
    start = next(i for i, r in enumerate(grid) if r and r[0] == header)
    rows = []
    for r in grid[start + 1 :]:
        if not r:
            break
        rows.append(r)
    return rows


# ---- column-letter and layout discovery ---------------------------------------------

def test_col_letter_covers_single_and_double_letters():
    assert _col_letter(0) == "A"
    assert _col_letter(6) == "G"
    assert _col_letter(26) == "AA"


def test_rep_layout_reads_column_positions_from_the_live_header():
    header = ["Date", "Prospect", "Disposition", "Phone", "Call ID", "ICP"]
    layout = _rep_layout(header, disposition_column="Disposition", icp_column="ICP")
    assert layout == RepLayout(date="A", disposition="C", icp="F")


def test_rep_layout_missing_required_column_returns_none():
    header = ["Prospect", "Disposition"]
    assert _rep_layout(header, disposition_column="Disposition", icp_column=None) is None


def test_rep_layout_missing_icp_column_is_allowed():
    header = ["Date", "Disposition"]
    layout = _rep_layout(header, disposition_column="Disposition", icp_column="ICP")
    assert layout.icp is None


# ---- ICP section ---------------------------------------------------------------------

def test_configured_icp_categories_write_countif_formulas_across_reps():
    b = _builder(icp_categories=["Founder", "VP Sales"])
    layouts = {"Rep A": LAYOUT, "Rep B": LAYOUT}
    grid = b.build_grid(layouts, {"Rep A": [], "Rep B": []})
    rows = _section(grid, "ICP Breakdown")[1:]  # skip column headers
    assert [r[0] for r in rows] == ["Founder", "VP Sales"]
    assert rows[0][1] == '=COUNTIF(\'Rep A\'!F2:F,"Founder")+COUNTIF(\'Rep B\'!F2:F,"Founder")'


def test_unconfigured_icp_categories_are_discovered_from_live_rows_by_count():
    b = _builder()
    rep_rows = {"Rep A": [_row(icp="Founder"), _row(icp="Founder"), _row(icp="CEO")]}
    grid = b.build_grid({"Rep A": LAYOUT}, rep_rows)
    rows = _section(grid, "ICP Breakdown")[1:]
    assert [r[0] for r in rows] == ["Founder", "CEO"]
    assert rows[0][1].startswith("=COUNTIF")


def test_rep_tab_without_an_icp_column_is_excluded_from_icp_formulas():
    b = _builder(icp_categories=["Founder"])
    layouts = {"Rep A": LAYOUT, "No ICP": RepLayout(date="A", disposition="C", icp=None)}
    grid = b.build_grid(layouts, {"Rep A": [], "No ICP": []})
    formula = _section(grid, "ICP Breakdown")[1][1]
    assert "Rep A" in formula and "No ICP" not in formula


# ---- meeting trends ------------------------------------------------------------------

def test_trends_write_one_row_per_week_oldest_first():
    b = _builder(trend_weeks=3)
    grid = b.build_grid({"Rep A": LAYOUT}, {"Rep A": []})
    rows = _section(grid, "Meeting Trends")[1:]
    assert len(rows) == 3
    assert "7*2" in rows[0][0] and "7*2" in rows[0][1]  # oldest week first
    assert "7*" not in rows[-1][0]  # current week last
    assert rows[0][1].startswith("=") and "SUMPRODUCT" in rows[0][1]
    assert '"Meeting Booked"' in rows[0][1]


def test_trends_cover_every_meeting_disposition_and_every_rep():
    b = _builder(meeting_dispositions=["Meeting Booked", "Rescheduled"])
    layouts = {"Rep A": LAYOUT, "Rep B": LAYOUT}
    grid = b.build_grid(layouts, {"Rep A": [], "Rep B": []})
    formula = _section(grid, "Meeting Trends")[1][1]
    for needle in ("'Rep A'", "'Rep B'", '"Meeting Booked"', '"Rescheduled"'):
        assert needle in formula


# ---- conversion rates ----------------------------------------------------------------

def test_rates_rows_are_formulas_with_row_relative_rate_cells():
    b = _builder()
    grid = b.build_grid({"Rep A": LAYOUT}, {"Rep A": []})
    rows = _section(grid, "Conversion Rates")
    rep_row = rows[1]  # after the column-header row
    sheet_row = next(i for i, r in enumerate(grid) if r and r[0] == "Rep A") + 1
    assert rep_row[1] == "=COUNTA('Rep A'!C2:C)"
    assert rep_row[3] == '=COUNTIF(\'Rep A\'!C2:C,"Meeting Booked")'
    # real numbers with a zero-denominator guard, not TEXT() strings, so the operator
    # can chart, sort, and percent-format them
    assert rep_row[4] == f"=IF(B{sheet_row}=0,0,D{sheet_row}/B{sheet_row})"
    assert rep_row[5] == f"=IF(C{sheet_row}=0,0,D{sheet_row}/C{sheet_row})"


def test_overall_row_sums_the_per_rep_cells_not_the_rates():
    b = _builder()
    layouts = {"Rep A": LAYOUT, "Rep B": LAYOUT}
    grid = b.build_grid(layouts, {"Rep A": [], "Rep B": []})
    overall = next(r for r in grid if r and r[0] == "Overall")
    assert overall[1].startswith("=SUM(B")
    assert overall[3].startswith("=SUM(D")
    overall_row = grid.index(overall) + 1
    assert f"D{overall_row}/B{overall_row}" in overall[4]


def test_no_qualified_set_makes_qualified_equal_conversations():
    b = _builder(qualified_dispositions=[])
    grid = b.build_grid({"Rep A": LAYOUT}, {"Rep A": []})
    rep_row = _section(grid, "Conversion Rates")[1]
    assert rep_row[2] == rep_row[1]  # both COUNTA of the disposition column


def test_reps_are_ranked_by_live_conversion_rate():
    b = _builder()
    rep_rows = {
        "Low": [_row("Interested"), _row("Interested"), _row("Meeting Booked")],
        "High": [_row("Meeting Booked")],
    }
    layouts = {"Low": LAYOUT, "High": LAYOUT}
    grid = b.build_grid(layouts, rep_rows)
    rows = _section(grid, "Conversion Rates")[1:]
    assert [r[0] for r in rows][:2] == ["High", "Low"]


# ---- leaderboard ---------------------------------------------------------------------

def test_leaderboard_metric_formulas_per_mode():
    layouts = {"Rep A": LAYOUT}
    rate = _builder().build_grid(layouts, {"Rep A": []})
    meetings = _builder(leaderboard_metric="meetings").build_grid(layouts, {"Rep A": []})
    calls = _builder(leaderboard_metric="calls").build_grid(layouts, {"Rep A": []})
    rate_value = _section(rate, "Rep Leaderboard")[1][1]
    assert rate_value.startswith("=IF((") and "TEXT" not in rate_value  # a real number
    assert _section(meetings, "Rep Leaderboard")[1][1] == '=COUNTIF(\'Rep A\'!C2:C,"Meeting Booked")'
    # calls = ALL tracked rows: counted on the always-populated Date column so the display
    # agrees with the ranking, which counts rows whether or not they have a disposition yet
    assert _section(calls, "Rep Leaderboard")[1][1] == "=COUNTA('Rep A'!A2:A)"


def test_unknown_leaderboard_metric_fails_fast():
    with pytest.raises(ValueError):
        _builder(leaderboard_metric="wins")


# ---- formula escaping and label safety ----------------------------------------------

def test_rep_names_with_apostrophes_and_quoted_dispositions_are_escaped():
    b = _builder(meeting_dispositions=['She said "yes"'])
    layouts = {"O'Brien": LAYOUT}
    grid = b.build_grid(layouts, {"O'Brien": []})
    rep_row = _section(grid, "Conversion Rates")[1]
    assert "'O''Brien'!" in rep_row[1]
    assert '"She said ""yes"""' in rep_row[3]


def test_countif_wildcards_in_labels_are_escaped_to_match_literally():
    b = _builder(meeting_dispositions=["Meet?ng*"], icp_categories=["VP*Sales"])
    grid = b.build_grid({"Rep A": LAYOUT}, {"Rep A": []})
    assert '"Meet~?ng~*"' in _section(grid, "Conversion Rates")[1][3]
    assert '"VP~*Sales"' in _section(grid, "ICP Breakdown")[1][1]


def test_discovered_category_labels_cannot_execute_as_formulas():
    # the label cell is apostrophe-guarded so USER_ENTERED writes it as text; the
    # COUNTIF criteria still quotes the original value
    b = _builder()
    rep_rows = {"Rep A": [_row(icp="=IMPORTRANGE(evil)"), _row(icp="1-10")]}
    grid = b.build_grid({"Rep A": LAYOUT}, rep_rows)
    labels = [r[0] for r in _section(grid, "ICP Breakdown")[1:]]
    assert "'=IMPORTRANGE(evil)" in labels
    assert "'1-10" in labels


def test_discovered_case_variants_merge_into_one_category():
    # COUNTIF matches case-insensitively, so "SaaS" + "Saas" rows would each double-count
    b = _builder()
    rep_rows = {"Rep A": [_row(icp="SaaS"), _row(icp="SaaS"), _row(icp="Saas")]}
    grid = b.build_grid({"Rep A": LAYOUT}, rep_rows)
    labels = [r[0] for r in _section(grid, "ICP Breakdown")[1:]]
    assert labels == ["SaaS"]


# ---- config validation ---------------------------------------------------------------

def test_string_list_fields_are_rejected_with_a_clear_error():
    with pytest.raises(ValueError, match="icp_categories"):
        _builder(icp_categories="Founder")


def test_trend_weeks_accepts_digit_strings_and_rejects_garbage():
    assert _builder(trend_weeks="4").trend_weeks == 4
    with pytest.raises(ValueError, match="trend_weeks"):
        _builder(trend_weeks="ten")
    with pytest.raises(ValueError, match="trend_weeks"):
        _builder(trend_weeks=-4)


def test_monday_safe_week_base():
    # WEEKDAY(TODAY(),3) maps Monday to 0; the WEEKDAY(TODAY()-1,2) idiom shifts the
    # whole trend window back a week whenever today is Monday
    b = _builder(trend_weeks=1)
    grid = b.build_grid({"Rep A": LAYOUT}, {"Rep A": []})
    label = _section(grid, "Meeting Trends")[1][0]
    assert "WEEKDAY(TODAY(),3)" in label
    assert "WEEKDAY(TODAY()-1,2)" not in label


# ---- rebuild_summary -----------------------------------------------------------------

def _config():
    return {
        "reps": {"Rep A": {"apollo_user_id": "u1"}},
        "stats": {
            "summary_tab": "Overall Statistics",
            "icp_column": "ICP",
            "meeting_dispositions": ["Meeting Booked"],
        },
    }


REP_HEADER = ["Date", "Prospect", "Disposition", "Phone", "Duration (sec)", "Call ID",
              "Recording URL", "ICP"]


def test_rebuild_writes_formulas_from_the_live_header_layout():
    sheet = FakeSheet()
    sheet.seed_row("Rep A", REP_HEADER, {"Date": "2026-05-20", "Prospect": "Jane",
                                         "Disposition": "Meeting Booked", "ICP": "Founder"})
    grid = rebuild_summary(_config(), sheet=sheet)
    assert grid is not None
    assert sheet.cleared == ["Overall Statistics"]
    written = sheet.grid("Overall Statistics")
    joined = "\n".join(str(c) for r in written for c in r)
    assert "'Rep A'!C2:C" in joined  # Disposition discovered at col C
    assert "'Rep A'!H2:H" in joined  # ICP discovered at col H


def test_rebuild_refuses_a_rep_tab_with_an_untrusted_layout():
    sheet = FakeSheet()
    sheet.seed_row("Rep A", ["Prospect", "Outcome"], {"Prospect": "Jane", "Outcome": "x"})
    with pytest.raises(ValueError):
        rebuild_summary(_config(), sheet=sheet)
    assert sheet.cleared == []  # nothing destroyed before the refusal


def test_rebuild_skips_when_all_reps_read_empty_but_summary_has_content():
    sheet = FakeSheet()
    sheet.ensure_header("Rep A", REP_HEADER)  # header exists, zero data rows
    sheet.grids["Overall Statistics"] = [["ICP Breakdown"]]  # populated summary
    assert rebuild_summary(_config(), sheet=sheet) is None
    assert sheet.cleared == []


def test_rebuild_proceeds_on_a_genuinely_fresh_sheet():
    sheet = FakeSheet()
    sheet.ensure_header("Rep A", REP_HEADER)
    grid = rebuild_summary(_config(), sheet=sheet)
    assert grid is not None
    assert sheet.grid("Overall Statistics")


def test_force_bypasses_the_all_empty_guard():
    # --stats-only: the operator is present, and the grid is rebuilt from config
    sheet = FakeSheet()
    sheet.ensure_header("Rep A", REP_HEADER)
    sheet.grids["Overall Statistics"] = [["ICP Breakdown"]]
    grid = rebuild_summary(_config(), sheet=sheet, force=True)
    assert grid is not None
    assert sheet.cleared == ["Overall Statistics"]


def test_rep_with_no_tab_yet_is_created_and_included_with_zeros():
    # a rep added to config before their first pull must not block the whole team's
    # summary, and their tab must exist so the formulas do not render #REF!
    sheet = FakeSheet()
    sheet.seed_row("Rep A", REP_HEADER, {"Date": "2026-05-20", "Prospect": "Jane",
                                         "Disposition": "Meeting Booked"})
    config = _config()
    config["reps"]["Rep C"] = {"apollo_user_id": "u3"}
    config["manual_columns"] = ["ICP"]
    grid = rebuild_summary(config, sheet=sheet)
    assert grid is not None
    assert sheet.header_row("Rep C")  # tab created with the pipeline's default header
    joined = "\n".join(str(c) for r in grid for c in r)
    assert "'Rep C'!" in joined  # included in the formulas, showing zeros until rows land
