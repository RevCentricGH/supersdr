"""StatsBuilder - rebuild the Overall Statistics summary tab from the live rep tabs."""
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

# Per-rep (or overall) conversion stats. meeting_rate = meetings / conversations;
# conversion_rate = meetings / qualified_conversations. Both are 0.0 when their denominator
# is 0, so a rep with no conversations never raises.
RepRates = namedtuple(
    "RepRates",
    ["rep", "conversations", "qualified_conversations", "meetings", "meeting_rate", "conversion_rate"],
)


def _format_pct(rate):
    """Format a 0..1 rate as a one-decimal percentage string (matches the reference tool)."""
    return f"{rate:.1%}"


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

    def __init__(self, *, icp_column, meeting_dispositions, leaderboard_metric="calls",
                 disposition_column=None, labels=None, qualified_dispositions=None):
        if leaderboard_metric not in self.LEADERBOARD_METRICS:
            raise ValueError(
                f"unknown leaderboard_metric {leaderboard_metric!r}; "
                f"valid: {', '.join(self.LEADERBOARD_METRICS)}"
            )
        self.icp_column = icp_column
        self.disposition_column = disposition_column or self.DEFAULT_DISPOSITION_COLUMN
        self.meeting_dispositions = {d.strip().lower() for d in meeting_dispositions if d and d.strip()}
        # When no qualified set is configured, every conversation counts as qualified, so the
        # conversion rate equals the meeting rate. Configure qualified_dispositions to narrow it.
        self.qualified_dispositions = {
            d.strip().lower() for d in (qualified_dispositions or []) if d and d.strip()
        }
        self.leaderboard_metric = leaderboard_metric
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
        )

    def icp_breakdown(self, rep_rows):
        counts = {}
        for rows in rep_rows.values():
            for row in rows:
                cat = (row.get(self.icp_column) or "").strip() if self.icp_column else ""
                if not cat:
                    continue
                counts[cat] = counts.get(cat, 0) + 1
        return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))

    def _disposition(self, row):
        return (row.get(self.disposition_column) or "").strip().lower()

    def _is_meeting(self, row):
        return self._disposition(row) in self.meeting_dispositions

    def _is_conversation(self, row):
        """A conversation is any row with a non-blank disposition (Apollo COUNTA of the column)."""
        return bool(self._disposition(row))

    def _is_qualified_conversation(self, row):
        disp = self._disposition(row)
        if not disp:
            return False
        # No qualified set configured: every conversation is qualified.
        return disp in self.qualified_dispositions if self.qualified_dispositions else True

    def _rep_rates(self, rep, rows):
        """Conversion stats for one rep's rows. Rates guard against a zero denominator."""
        conversations = sum(1 for r in rows if self._is_conversation(r))
        qualified = sum(1 for r in rows if self._is_qualified_conversation(r))
        meetings = sum(1 for r in rows if self._is_meeting(r))
        meeting_rate = meetings / conversations if conversations else 0.0
        conversion_rate = meetings / qualified if qualified else 0.0
        return RepRates(rep, conversations, qualified, meetings, meeting_rate, conversion_rate)

    def conversion_rates(self, rep_rows):
        """Per-rep RepRates, ranked by conversion rate (then meetings, then name) descending.

        Excludes the overall aggregate so callers never have to skip a trailing row; use
        ``overall_rates`` for the team total.
        """
        rates = [self._rep_rates(rep, rows) for rep, rows in rep_rows.items()]
        rates.sort(key=lambda rr: (-rr.conversion_rate, -rr.meetings, rr.rep))
        return rates

    def overall_rates(self, rep_rows):
        """Team total. Rates are summed-numerator over summed-denominator, NOT the mean of the
        per-rep rates, so a low-volume rep cannot skew the overall conversion rate."""
        conversations = qualified = meetings = 0
        for rows in rep_rows.values():
            conversations += sum(1 for r in rows if self._is_conversation(r))
            qualified += sum(1 for r in rows if self._is_qualified_conversation(r))
            meetings += sum(1 for r in rows if self._is_meeting(r))
        meeting_rate = meetings / conversations if conversations else 0.0
        conversion_rate = meetings / qualified if qualified else 0.0
        return RepRates(self.labels["rates_overall_row"], conversations, qualified, meetings,
                        meeting_rate, conversion_rate)

    def meeting_trends(self, rep_rows):
        weeks = {}
        for rows in rep_rows.values():
            for row in rows:
                if not self._is_meeting(row):
                    continue
                week = _iso_week(row.get("Date"))
                if not week:
                    continue
                weeks[week] = weeks.get(week, 0) + 1
        return sorted(weeks.items())

    def leaderboard(self, rep_rows):
        if self.leaderboard_metric == "rate":
            # Rank by conversion rate, so efficiency wins over raw volume. conversion_rates is
            # already ordered (rate, then meetings, then name); the value shown is the rate.
            return [(rr.rep, rr.conversion_rate) for rr in self.conversion_rates(rep_rows)]
        out = []
        for rep, rows in rep_rows.items():
            if self.leaderboard_metric == "meetings":
                value = sum(1 for r in rows if self._is_meeting(r))
            else:
                value = len(rows)
            out.append((rep, value))
        out.sort(key=lambda kv: (-kv[1], kv[0]))
        return out

    def build_grid(self, rep_rows):
        """Assemble the full summary tab as a 2D block: three labeled sections, in order."""
        labels = self.labels
        grid = []
        grid.append([labels["icp_header"]])
        grid.append([labels["icp_category_col"], labels["icp_count_col"]])
        for category, count in self.icp_breakdown(rep_rows):
            grid.append([category, count])
        grid.append([])
        grid.append([labels["trends_header"]])
        grid.append([labels["trends_week_col"], labels["trends_count_col"]])
        for week, count in self.meeting_trends(rep_rows):
            grid.append([week, count])
        grid.append([])
        grid.append([labels["rates_header"]])
        grid.append([labels["rates_rep_col"], labels["rates_conversations_col"],
                     labels["rates_qualified_col"], labels["rates_meetings_col"],
                     labels["rates_meeting_rate_col"], labels["rates_conversion_rate_col"]])
        for rr in self.conversion_rates(rep_rows):
            grid.append([rr.rep, rr.conversations, rr.qualified_conversations, rr.meetings,
                         _format_pct(rr.meeting_rate), _format_pct(rr.conversion_rate)])
        overall = self.overall_rates(rep_rows)
        grid.append([overall.rep, overall.conversations, overall.qualified_conversations,
                     overall.meetings, _format_pct(overall.meeting_rate),
                     _format_pct(overall.conversion_rate)])
        grid.append([])
        grid.append([labels["leaderboard_header"]])
        grid.append([labels["leaderboard_rep_col"], labels["leaderboard_metric_col"]])
        for rep, value in self.leaderboard(rep_rows):
            grid.append([rep, _format_pct(value) if self.leaderboard_metric == "rate" else value])
        return grid


def rebuild_summary(config, *, sheet, builder=None):
    """Read every configured rep tab live, rebuild the summary grid, and write it.

    Precondition: ``config["stats"]["summary_tab"]`` must be set. run.py only calls this when
    a ``stats`` block is present; if it is missing this raises a clear ``ValueError`` rather
    than a bare ``KeyError``.

    Clears the summary tab before writing so stale rows from a previous, larger run never
    persist; reading live each time means the summary always reflects the current rep tabs.
    Returns the grid that was written.
    """
    builder = builder or StatsBuilder.from_config(config)
    summary_tab = (config.get("stats") or {}).get("summary_tab")
    if not summary_tab:
        raise ValueError("rebuild_summary requires config['stats']['summary_tab']")
    rep_rows = {rep_name: sheet.read_rows(rep_name) for rep_name in config["reps"]}
    grid = builder.build_grid(rep_rows)
    sheet.clear_tab(summary_tab)
    sheet.write_grid(summary_tab, grid)
    return grid
