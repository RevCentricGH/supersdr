"""In-memory fakes standing in for the side-effecting wrappers, so pipeline tests run
without a live Apollo account or Google Sheet."""


class FakeSheet:
    """Models per-tab rows as dicts keyed by header. existing_keys is derived from the
    stored rows directly (contract 18), and append never rewrites a row (so manual
    columns on existing rows are untouched)."""

    def __init__(self, fail_on_call_id=None):
        self.tabs = {}  # tab -> {"header": [...], "rows": [ {col: val} ]}
        self.fail_on_call_id = fail_on_call_id
        self.grids = {}  # tab -> [ [cell, ...], ... ] for raw-grid tabs (the summary tab)
        self.cleared = []  # tabs clear_tab was called on, in order

    def ensure_header(self, tab, header):
        self.tabs.setdefault(tab, {"header": list(header), "rows": []})

    def existing_keys(self, tab):
        t = self.tabs.get(tab)
        if not t:
            return set()
        keys = set()
        for r in t["rows"]:
            keys.add((r.get("Date", ""), (r.get("Prospect", "") or "").strip().lower()))
        return keys

    def append_row(self, tab, values_list):
        t = self.tabs[tab]
        row = dict(zip(t["header"], values_list))
        if self.fail_on_call_id and row.get("Call ID") == self.fail_on_call_id:
            raise RuntimeError("simulated sheet write failure")
        t["rows"].append(row)

    # --- read/clear/write surface StatsBuilder uses on the live sheet ---

    def read_rows(self, tab):
        """Return a rep tab's data rows as header-keyed dicts (empty for a missing tab)."""
        return [dict(r) for r in self.tabs.get(tab, {}).get("rows", [])]

    def clear_tab(self, tab):
        self.cleared.append(tab)
        self.grids[tab] = []

    def write_grid(self, tab, values_2d):
        """Overlay values starting at the top, like Sheets values.update at A1: cells beyond
        the written range are left intact, so a stale row only disappears if clear_tab ran."""
        grid = self.grids.setdefault(tab, [])
        for i, row in enumerate(values_2d):
            if i < len(grid):
                grid[i] = list(row)
            else:
                grid.append(list(row))

    # convenience for assertions
    def prospects(self, tab):
        return [r.get("Prospect") for r in self.tabs.get(tab, {}).get("rows", [])]

    def grid(self, tab):
        return self.grids.get(tab, [])

    def seed_row(self, tab, header, row):
        self.ensure_header(tab, header)
        self.tabs[tab]["rows"].append(dict(row))


class FakeApollo:
    """Returns per-rep calls keyed by the rep's apollo user id."""

    def __init__(self, calls_by_user):
        self.calls_by_user = calls_by_user
        self.searched = []

    def search_calls(self, rep_cfg, since=None):
        self.searched.append((rep_cfg.get("apollo_user_id"), since))
        return list(self.calls_by_user.get(rep_cfg.get("apollo_user_id"), []))
