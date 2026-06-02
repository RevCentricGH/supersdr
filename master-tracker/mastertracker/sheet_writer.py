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
        """Write a 2D block starting at A1 (the summary tab is rebuilt wholesale each run)."""
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
        meta = self.service.get(spreadsheetId=self.spreadsheet_id).execute()
        titles = {s["properties"]["title"] for s in meta.get("sheets", [])}
        if tab in titles:
            return
        self.service.batchUpdate(
            spreadsheetId=self.spreadsheet_id,
            body={"requests": [{"addSheet": {"properties": {"title": tab}}}]},
        ).execute()
