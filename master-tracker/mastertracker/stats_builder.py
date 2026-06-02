"""StatsBuilder - rebuild the Overall Statistics summary tab from the live rep tabs."""
import datetime

# Generic English fallbacks. Every label is overridable from config; none names a specific
# organization, team, or rep, so the skill works unchanged for any operator.
DEFAULT_LABELS = {
    "icp_header": "ICP Breakdown",
    "icp_category_col": "ICP",
    "icp_count_col": "Count",
    "trends_header": "Meeting Trends",
    "trends_week_col": "Week",
    "trends_count_col": "Meetings",
    "leaderboard_header": "Rep Leaderboard",
    "leaderboard_rep_col": "Rep",
    "leaderboard_metric_col": "Activity",
}


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
    LEADERBOARD_METRICS = ("calls", "meetings")
    DEFAULT_DISPOSITION_COLUMN = "Disposition"

    def __init__(self, *, icp_column, meeting_dispositions, leaderboard_metric="calls",
                 disposition_column=None, labels=None):
        if leaderboard_metric not in self.LEADERBOARD_METRICS:
            raise ValueError(
                f"unknown leaderboard_metric {leaderboard_metric!r}; "
                f"valid: {', '.join(self.LEADERBOARD_METRICS)}"
            )
        self.icp_column = icp_column
        self.disposition_column = disposition_column or self.DEFAULT_DISPOSITION_COLUMN
        self.meeting_dispositions = {d.strip().lower() for d in meeting_dispositions if d and d.strip()}
        self.leaderboard_metric = leaderboard_metric
        self.labels = {**DEFAULT_LABELS, **(labels or {})}

    @classmethod
    def from_config(cls, config):
        stats = config.get("stats", {})
        return cls(
            icp_column=stats.get("icp_column"),
            meeting_dispositions=stats.get("meeting_dispositions", []),
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

    def _is_meeting(self, row):
        return (row.get(self.disposition_column) or "").strip().lower() in self.meeting_dispositions

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
        grid.append([labels["leaderboard_header"]])
        grid.append([labels["leaderboard_rep_col"], labels["leaderboard_metric_col"]])
        for rep, value in self.leaderboard(rep_rows):
            grid.append([rep, value])
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
