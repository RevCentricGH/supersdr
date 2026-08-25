"""StatsBuilder - build the Overall Statistics summary tab as LIVE formulas.

The summary is written once per rebuild as Google Sheets formulas (COUNTIF, COUNTA,
SUMPRODUCT) that reference the rep tabs, not as numbers computed in Python. Between
rebuilds the tab keeps itself current as rep tabs change. A rebuild is only needed when
the shape changes: a rep added or renamed, a new ICP category, changed dispositions.

The writer only ever touches cell VALUES in the summary grid. Formatting - colors,
fonts, borders, widths, conditional formats - is set up once by ``--scaffold`` and then
owned by the operator, so anyone can restyle the tracker without a refresh undoing it.
"""
import datetime
from collections import namedtuple

# Generic English fallbacks. Every label is overridable from config; none names a specific
# organization, team, or rep, so the skill works unchanged for any operator.
DEFAULT_LABELS = {
    "icp_header": "ICP Breakdown",
    "icp_category_col": "ICP",
    "icp_count_col": "Count",
    "trends_header": "Meeting Trends",
    "trends_week_col": "Week",
    "trends_count_col": "Meetings",
    "rates_header": "Conversion Rates",
    "rates_rep_col": "Rep",
    "rates_conversations_col": "Conversations",
    "rates_qualified_col": "Qualified Conversations",
    "rates_meetings_col": "Meetings",
    "rates_meeting_rate_col": "Meeting Rate",
    "rates_conversion_rate_col": "Conversion Rate",
    "rates_overall_row": "Overall",
    "leaderboard_header": "Rep Leaderboard",
    "leaderboard_rep_col": "Rep",
    "leaderboard_metric_col": "Activity",
}

# Per-rep (or overall) conversion stats, computed from live-read rows. Only used to ORDER
# the rates section and leaderboard at rebuild time; the numbers written to the sheet are
# formulas. meeting_rate = meetings / conversations; conversion_rate = meetings /
# qualified_conversations. Both are 0.0 when their denominator is 0.
RepRates = namedtuple(
    "RepRates",
    ["rep", "conversations", "qualified_conversations", "meetings", "meeting_rate", "conversion_rate"],
)

# Column letters each rep tab's formulas are built from, discovered from that tab's live
# header row so an operator who moved or added columns still gets correct formulas.
# icp is None when the tab has no ICP column (that rep is skipped by the ICP section).
RepLayout = namedtuple("RepLayout", ["date", "disposition", "icp"])


def _col_letter(index):
    """0-indexed column position -> A1 letter."""
    out = ""
    index += 1
    while index:
        index, rem = divmod(index - 1, 26)
        out = chr(65 + rem) + out
    return out


def _tab_ref(tab):
    """A1 tab reference, with embedded apostrophes escaped."""
    return "'" + tab.replace("'", "''") + "'"


def _quote(text):
    """Double-quote a formula string literal, escaping embedded quotes."""
    return '"' + str(text).replace('"', '""') + '"'


def _iso_week(date_str):
    """Map a YYYY-MM-DD cell to a sortable ISO year-week label, or None if unparseable."""
    if not date_str:
        return None
    try:
        d = datetime.date.fromisoformat(str(date_str).strip()[:10])
    except ValueError:
        return None
    iso = d.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


class StatsBuilder:
    LEADERBOARD_METRICS = ("calls", "meetings", "rate")
    DEFAULT_DISPOSITION_COLUMN = "Disposition"
    DEFAULT_TREND_WEEKS = 10

    def __init__(self, *, icp_column, meeting_dispositions, leaderboard_metric="calls",
                 disposition_column=None, labels=None, qualified_dispositions=None,
                 icp_categories=None, trend_weeks=None):
        if leaderboard_metric not in self.LEADERBOARD_METRICS:
            raise ValueError(
                f"unknown leaderboard_metric {leaderboard_metric!r}; "
                f"valid: {', '.join(self.LEADERBOARD_METRICS)}"
            )
        self.icp_column = icp_column
        self.disposition_column = disposition_column or self.DEFAULT_DISPOSITION_COLUMN
        # Preserve configured order and casing for the formulas; the lowercased sets are
        # only for classifying live-read rows when ordering sections.
        self.meeting_disposition_list = [d.strip() for d in meeting_dispositions if d and d.strip()]
        self.meeting_dispositions = {d.lower() for d in self.meeting_disposition_list}
        self.qualified_disposition_list = [
            d.strip() for d in (qualified_dispositions or []) if d and d.strip()
        ]
        self.qualified_dispositions = {d.lower() for d in self.qualified_disposition_list}
        self.leaderboard_metric = leaderboard_metric
        # A fixed category list writes stable formulas; without one, categories are
        # discovered from the live rows at each rebuild (new categories appear on the
        # next rebuild rather than live).
        self.icp_categories = [c.strip() for c in (icp_categories or []) if c and c.strip()]
        self.trend_weeks = trend_weeks or self.DEFAULT_TREND_WEEKS
        self.labels = {**DEFAULT_LABELS, **(labels or {})}

    @classmethod
    def from_config(cls, config):
        stats = config.get("stats", {})
        return cls(
            icp_column=stats.get("icp_column"),
            meeting_dispositions=stats.get("meeting_dispositions", []),
            qualified_dispositions=stats.get("qualified_dispositions", []),
            leaderboard_metric=stats.get("leaderboard_metric", "calls"),
            disposition_column=stats.get("disposition_column"),
            labels=stats.get("labels"),
            icp_categories=stats.get("icp_categories"),
            trend_weeks=stats.get("trend_weeks"),
        )

    # ---- formula fragments (no leading =) ------------------------------------------

    def _dispo_range(self, rep, layout):
        col = layout.disposition
        return f"{_tab_ref(rep)}!{col}2:{col}"

    def _date_range(self, rep, layout):
        col = layout.date
        return f"{_tab_ref(rep)}!{col}2:{col}"

    def _count_dispo(self, rep, layout, dispo):
        return f"COUNTIF({self._dispo_range(rep, layout)},{_quote(dispo)})"

    def _conversations(self, rep, layout):
        return f"COUNTA({self._dispo_range(rep, layout)})"

    def _meetings(self, rep, layout):
        if not self.meeting_disposition_list:
            return "0"
        return "+".join(self._count_dispo(rep, layout, d) for d in self.meeting_disposition_list)

    def _qualified(self, rep, layout):
        # No qualified set configured: every conversation is qualified.
        if not self.qualified_disposition_list:
            return self._conversations(rep, layout)
        return "+".join(self._count_dispo(rep, layout, d) for d in self.qualified_disposition_list)

    def _icp_count(self, category, layouts):
        parts = []
        for rep, layout in layouts.items():
            if not layout.icp:
                continue
            col = layout.icp
            parts.append(f"COUNTIF({_tab_ref(rep)}!{col}2:{col},{_quote(category)})")
        return "=" + "+".join(parts) if parts else "0"

    def _week_base(self, weeks_ago):
        # Monday of the current ISO week, minus N weeks.
        base = "TODAY()-WEEKDAY(TODAY()-1,2)"
        return f"{base}-7*{weeks_ago}" if weeks_ago else base

    def _week_label(self, weeks_ago):
        base = self._week_base(weeks_ago)
        return f'=TEXT({base},"M/D")&" - "&TEXT({base}+6,"M/D")'

    def _week_meetings(self, weeks_ago, layouts):
        if not self.meeting_disposition_list:
            return "0"
        base = self._week_base(weeks_ago)
        parts = []
        for rep, layout in layouts.items():
            dates = self._date_range(rep, layout)
            dispo = self._dispo_range(rep, layout)
            is_meeting = "+".join(
                f"({dispo}={_quote(d)})" for d in self.meeting_disposition_list
            )
            parts.append(f"SUMPRODUCT(({dates}>={base})*({dates}<={base}+6)*({is_meeting}))")
        return "=" + "+".join(parts)

    # ---- live-read helpers (ordering + ICP discovery only) --------------------------

    def _disposition(self, row):
        return (row.get(self.disposition_column) or "").strip().lower()

    def _is_meeting(self, row):
        return self._disposition(row) in self.meeting_dispositions

    def _is_conversation(self, row):
        return bool(self._disposition(row))

    def _is_qualified_conversation(self, row):
        disp = self._disposition(row)
        if not disp:
            return False
        return disp in self.qualified_dispositions if self.qualified_dispositions else True

    def _rep_rates(self, rep, rows):
        conversations = sum(1 for r in rows if self._is_conversation(r))
        qualified = sum(1 for r in rows if self._is_qualified_conversation(r))
        meetings = sum(1 for r in rows if self._is_meeting(r))
        meeting_rate = meetings / conversations if conversations else 0.0
        conversion_rate = meetings / qualified if qualified else 0.0
        return RepRates(rep, conversations, qualified, meetings, meeting_rate, conversion_rate)

    def ranked_reps(self, rep_rows):
        """Rep names ordered for the rates section and leaderboard: by conversion rate,
        then meetings, then name, from the rows read at rebuild time. The displayed
        numbers are formulas; only this ORDER is frozen until the next rebuild."""
        rates = [self._rep_rates(rep, rows) for rep, rows in rep_rows.items()]
        if self.leaderboard_metric == "meetings":
            rates.sort(key=lambda rr: (-rr.meetings, rr.rep))
        elif self.leaderboard_metric == "calls":
            rates.sort(key=lambda rr: (-len(rep_rows[rr.rep]), rr.rep))
        else:
            rates.sort(key=lambda rr: (-rr.conversion_rate, -rr.meetings, rr.rep))
        return [rr.rep for rr in rates]

    def icp_category_list(self, rep_rows):
        """The configured category list, or categories discovered from the live rows
        (by descending count) when none is configured."""
        if self.icp_categories:
            return list(self.icp_categories)
        counts = {}
        for rows in rep_rows.values():
            for row in rows:
                cat = (row.get(self.icp_column) or "").strip() if self.icp_column else ""
                if not cat:
                    continue
                counts[cat] = counts.get(cat, 0) + 1
        return [cat for cat, _ in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))]

    def _leaderboard_value(self, rep, layout):
        if self.leaderboard_metric == "meetings":
            return "=" + self._meetings(rep, layout)
        if self.leaderboard_metric == "calls":
            return "=" + self._conversations(rep, layout)
        meetings = self._meetings(rep, layout)
        qualified = self._qualified(rep, layout)
        return f'=IF(({qualified})=0,"0.0%",TEXT(({meetings})/({qualified}),"0.0%"))'

    # ---- grid assembly ---------------------------------------------------------------

    def build_grid(self, layouts, rep_rows):
        """Assemble the summary as a 2D block of labels and formulas.

        ``layouts`` maps rep name -> RepLayout (that tab's live column letters);
        ``rep_rows`` maps rep name -> rows read at rebuild time, used only to order
        sections and (without a configured list) discover ICP categories.
        """
        labels = self.labels
        grid = []

        grid.append([labels["icp_header"]])
        grid.append([labels["icp_category_col"], labels["icp_count_col"]])
        for category in self.icp_category_list(rep_rows):
            grid.append([category, self._icp_count(category, layouts)])

        grid.append([])
        grid.append([labels["trends_header"]])
        grid.append([labels["trends_week_col"], labels["trends_count_col"]])
        # Oldest week first, current week last, so the trend reads left-to-right in time.
        for weeks_ago in range(self.trend_weeks - 1, -1, -1):
            grid.append([self._week_label(weeks_ago), self._week_meetings(weeks_ago, layouts)])

        grid.append([])
        grid.append([labels["rates_header"]])
        grid.append([labels["rates_rep_col"], labels["rates_conversations_col"],
                     labels["rates_qualified_col"], labels["rates_meetings_col"],
                     labels["rates_meeting_rate_col"], labels["rates_conversion_rate_col"]])
        ranked = self.ranked_reps(rep_rows)
        first_data_row = len(grid) + 1  # 1-indexed sheet row of the first rep line
        for offset, rep in enumerate(ranked):
            row_num = first_data_row + offset
            layout = layouts[rep]
            grid.append([
                rep,
                "=" + self._conversations(rep, layout),
                "=" + self._qualified(rep, layout),
                "=" + self._meetings(rep, layout),
                f'=IF(B{row_num}=0,"0.0%",TEXT(D{row_num}/B{row_num},"0.0%"))',
                f'=IF(C{row_num}=0,"0.0%",TEXT(D{row_num}/C{row_num},"0.0%"))',
            ])
        # Overall row: summed numerators over summed denominators via the cells above,
        # NOT the mean of per-rep rates, so a low-volume rep cannot skew it.
        overall_row = first_data_row + len(ranked)
        last_data_row = overall_row - 1
        if ranked:
            grid.append([
                labels["rates_overall_row"],
                f"=SUM(B{first_data_row}:B{last_data_row})",
                f"=SUM(C{first_data_row}:C{last_data_row})",
                f"=SUM(D{first_data_row}:D{last_data_row})",
                f'=IF(B{overall_row}=0,"0.0%",TEXT(D{overall_row}/B{overall_row},"0.0%"))',
                f'=IF(C{overall_row}=0,"0.0%",TEXT(D{overall_row}/C{overall_row},"0.0%"))',
            ])

        grid.append([])
        grid.append([labels["leaderboard_header"]])
        grid.append([labels["leaderboard_rep_col"], labels["leaderboard_metric_col"]])
        for rep in ranked:
            grid.append([rep, self._leaderboard_value(rep, layouts[rep])])
        return grid


def _rep_layout(header, *, disposition_column, icp_column):
    """Column letters for one rep tab from its live header row. Date and the disposition
    column are required (formulas would silently count the wrong column otherwise); a
    missing ICP column just excludes that tab from the ICP section."""
    positions = {name: i for i, name in enumerate(header)}
    if "Date" not in positions or disposition_column not in positions:
        return None
    icp = _col_letter(positions[icp_column]) if icp_column and icp_column in positions else None
    return RepLayout(
        date=_col_letter(positions["Date"]),
        disposition=_col_letter(positions[disposition_column]),
        icp=icp,
    )


def rebuild_summary(config, *, sheet, builder=None):
    """Read each rep tab's header and rows, then write the summary grid of live formulas.

    Precondition: ``config["stats"]["summary_tab"]`` must be set. run.py only calls this
    when a ``stats`` block is present.

    Abort-loudly guards (never destroy a populated summary on a suspicious read):
    - a rep tab whose header lacks Date or the disposition column stops the rebuild
      before anything is cleared, naming the tab;
    - if every rep tab reads back empty but the summary tab has content, the rebuild is
      skipped: an all-empty read is far more likely a failed or quota-capped read than
      a genuinely empty tracker.

    Clears only values (formatting survives) before writing, so stale rows from a
    previous, larger layout never linger. Returns the grid that was written, or None
    when the all-empty guard skipped the rebuild.
    """
    builder = builder or StatsBuilder.from_config(config)
    summary_tab = (config.get("stats") or {}).get("summary_tab")
    if not summary_tab:
        raise ValueError("rebuild_summary requires config['stats']['summary_tab']")

    layouts, rep_rows = {}, {}
    for rep_name in config["reps"]:
        header = sheet.header_row(rep_name)
        layout = _rep_layout(
            header,
            disposition_column=builder.disposition_column,
            icp_column=builder.icp_column,
        )
        if layout is None:
            raise ValueError(
                f"rep tab {rep_name!r} is missing a 'Date' or "
                f"{builder.disposition_column!r} column; refusing to rebuild the summary "
                "against a tab whose layout the formulas cannot trust"
            )
        layouts[rep_name] = layout
        rep_rows[rep_name] = sheet.read_rows(rep_name)

    if rep_rows and all(not rows for rows in rep_rows.values()) and sheet.has_content(summary_tab):
        return None

    grid = builder.build_grid(layouts, rep_rows)
    sheet.clear_tab(summary_tab)
    sheet.write_grid(summary_tab, grid)
    return grid
