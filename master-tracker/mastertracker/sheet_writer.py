"""SheetWriter - append-only merge into per-rep tabs of a Google Sheet.

Thin by design and validated by the manual end-to-end run, not unit tests. Two invariants
the pure modules depend on:

  - ``existing_keys`` reads the live sheet rows and returns (date, lowercased prospect) for
    each, so dedup is decided from the sheet, never from local state.
  - ``append_row`` only ever appends. Existing rows - and therefore any manual columns the
    operator filled in - are never rewritten.

The Sheets service is injected so this module never builds credentials itself; run.py wires
the OAuth flow and hands in a built ``spreadsheets()`` service.
"""


class SheetWriter:
    def __init__(self, service, spreadsheet_id):
        self.service = service
        self.spreadsheet_id = spreadsheet_id
        self._headers = {}  # tab -> header list

    def ensure_header(self, tab, header):
        self._add_tab_if_missing(tab)
        first_row = self._get_values(f"{tab}!1:1")
        if not first_row or not first_row[0]:
            self.service.values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"{tab}!A1",
                valueInputOption="USER_ENTERED",
                body={"values": [header]},
            ).execute()
            self._headers[tab] = list(header)
        else:
            self._headers[tab] = first_row[0]

    def existing_keys(self, tab):
        rows = self._get_values(f"{tab}!A1:ZZ")
        if not rows:
            return set()
        header = rows[0]
        try:
            date_i = header.index("Date")
            prospect_i = header.index("Prospect")
        except ValueError:
            return set()
        keys = set()
        for row in rows[1:]:
            date = row[date_i] if date_i < len(row) else ""
            prospect = row[prospect_i] if prospect_i < len(row) else ""
            keys.add((date, (prospect or "").strip().lower()))
        return keys

    def append_row(self, tab, values_list):
        self.service.values().append(
            spreadsheetId=self.spreadsheet_id,
            range=f"{tab}!A1",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": [values_list]},
        ).execute()

    def read_rows(self, tab):
        """Read a tab's data rows as header-keyed dicts. StatsBuilder reads the live rep
        tabs through this, so the summary always reflects what is in the sheet right now."""
        rows = self._get_values(f"{tab}!A1:ZZ")
        if not rows:
            return []
        header = rows[0]
        out = []
        for row in rows[1:]:
            out.append({col: (row[i] if i < len(row) else "") for i, col in enumerate(header)})
        return out

    def header_row(self, tab):
        """The tab's live header row (empty list for a missing or blank tab). StatsBuilder
        derives each rep tab's column letters from this, so formulas stay correct for an
        operator who moved or added columns. Checked via metadata first: a values read on
        a nonexistent tab raises instead of returning empty, and the missing-tab case must
        reach the caller's create-with-default-header fallback, not crash."""
        if self._sheet_id(tab) is None:
            return []
        first_row = self._get_values(f"{tab}!1:1")
        return first_row[0] if first_row else []

    def has_content(self, tab):
        """True when the tab exists and holds any value at all. The summary rebuild's
        anti-wipe guard: never clear a populated summary on an all-empty rep read. A tab
        that does not exist yet has no content - checked via metadata first, because a
        values read on a nonexistent tab raises instead of returning empty."""
        if self._sheet_id(tab) is None:
            return False
        return bool(self._get_values(f"{tab}!A1:ZZ"))

    def style_header_once(self, tab):
        """One-time scaffold styling: bold and freeze the header row, creating the tab
        first if needed so a scaffold on a fresh spreadsheet styles real tabs instead of
        silently doing nothing. Never called on the recurring path - formatting is the
        operator's after this."""
        self._add_tab_if_missing(tab)
        sheet_id = self._sheet_id(tab)
        if sheet_id is None:
            # Tab vanished between the two metadata reads. A null sheetId would silently
            # format the spreadsheet's FIRST sheet; failing loudly is the only safe move.
            raise RuntimeError(f"tab {tab!r} disappeared while styling it; rerun --scaffold")
        self.service.batchUpdate(
            spreadsheetId=self.spreadsheet_id,
            body={"requests": [
                {"repeatCell": {
                    "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1},
                    "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
                    "fields": "userEnteredFormat.textFormat.bold",
                }},
                {"updateSheetProperties": {
                    "properties": {"sheetId": sheet_id, "gridProperties": {"frozenRowCount": 1}},
                    "fields": "gridProperties.frozenRowCount",
                }},
            ]},
        ).execute()

    def percent_format_columns_once(self, tab, first_col_index, last_col_index):
        """One-time scaffold styling: a percent number format on whole columns (0-indexed,
        end exclusive). The rebuild writes rates as plain numbers; this makes them display
        as percentages without the recurring path ever touching formatting."""
        self._add_tab_if_missing(tab)
        sheet_id = self._sheet_id(tab)
        if sheet_id is None:
            raise RuntimeError(f"tab {tab!r} disappeared while styling it; rerun --scaffold")
        self.service.batchUpdate(
            spreadsheetId=self.spreadsheet_id,
            body={"requests": [
                {"repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startColumnIndex": first_col_index,
                        "endColumnIndex": last_col_index,
                    },
                    "cell": {"userEnteredFormat": {
                        "numberFormat": {"type": "PERCENT", "pattern": "0.0%"},
                    }},
                    "fields": "userEnteredFormat.numberFormat",
                }},
            ]},
        ).execute()

    def _sheet_id(self, tab):
        # Case-insensitive to match how Sheets treats tab names in A1 ranges, so a
        # config name differing only in case still finds the real tab.
        meta = self.service.get(spreadsheetId=self.spreadsheet_id).execute()
        for s in meta.get("sheets", []):
            if s["properties"]["title"].casefold() == tab.casefold():
                return s["properties"]["sheetId"]
        return None

    def clear_tab(self, tab):
        """Clear every value in a tab. Called before writing the summary so stale rows from
        a previous, larger run never linger below the new content."""
        self._add_tab_if_missing(tab)
        self.service.values().clear(
            spreadsheetId=self.spreadsheet_id,
            range=f"{tab}!A1:ZZ",
            body={},
        ).execute()

    def write_grid(self, tab, values_2d):
        """Write a 2D block starting at A1. USER_ENTERED so the summary's live formulas
        are entered as formulas; values.update touches cell values only, never
        formatting, so the operator's styling survives every rebuild."""
        self._add_tab_if_missing(tab)
        self.service.values().update(
            spreadsheetId=self.spreadsheet_id,
            range=f"{tab}!A1",
            valueInputOption="USER_ENTERED",
            body={"values": values_2d},
        ).execute()

    def _get_values(self, rng):
        resp = (
            self.service.values()
            .get(spreadsheetId=self.spreadsheet_id, range=rng)
            .execute()
        )
        return resp.get("values", [])

    def _add_tab_if_missing(self, tab):
        # Sheets tab names are unique case-insensitively, so the existence check must be
        # too: an exact-case check misses 'REP A' vs 'Rep A' and the addSheet then 400s.
        meta = self.service.get(spreadsheetId=self.spreadsheet_id).execute()
        titles = {s["properties"]["title"].casefold() for s in meta.get("sheets", [])}
        if tab.casefold() in titles:
            return
        self.service.batchUpdate(
            spreadsheetId=self.spreadsheet_id,
            body={"requests": [{"addSheet": {"properties": {"title": tab}}}]},
        ).execute()
