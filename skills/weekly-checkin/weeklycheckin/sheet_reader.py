"""SheetReader - read a master-tracker rep tab's rows for a given week.

Read-only: this skill never writes to the sheet. The Sheets service is injected (same pattern
as master-tracker's SheetWriter) so this module never builds credentials itself; run.py wires
the OAuth flow and hands in a built ``spreadsheets()`` service.

For a tab, ``read_week`` reads the rows, finds the ``Date`` and ``Disposition`` columns (header
whitespace is stripped before lookup), parses each ``Date`` as an ISO date, keeps the rows whose
date falls in [start, end], and returns them as header-keyed dicts. Rows with an empty ``Date``
or ``Disposition`` are skipped. A configured tab that is not in the sheet, a tab missing the
``Date`` or ``Disposition`` header, or an unparseable date all fail fast with the offending name
or value. Sheet dates are compared as naive ``date`` objects (assumed UTC-naive, as written by
master-tracker).
"""
import datetime

DATE_COLUMN = "Date"
DISPOSITION_COLUMN = "Disposition"


class SheetReaderError(RuntimeError):
    pass


class SheetReader:
    def __init__(self, service, spreadsheet_id):
        self.service = service
        self.spreadsheet_id = spreadsheet_id
        self._titles = None

    def read_week(self, tab, start_date, end_date):
        self._assert_tab_exists(tab)
        rows = self._get_values(f"{tab}!A1:ZZ")
        if not rows:
            return []
        header = [h.strip() for h in rows[0]]
        date_i = self._column_index(header, DATE_COLUMN, tab)
        disp_i = self._column_index(header, DISPOSITION_COLUMN, tab)
        out = []
        for row in rows[1:]:
            date_raw = (row[date_i] if date_i < len(row) else "").strip()
            disp_raw = (row[disp_i] if disp_i < len(row) else "").strip()
            if not date_raw or not disp_raw:
                continue
            try:
                parsed = datetime.date.fromisoformat(date_raw)
            except ValueError:
                raise SheetReaderError(
                    f"tab '{tab}' has an unparseable {DATE_COLUMN} value '{date_raw}'"
                )
            if parsed < start_date or parsed > end_date:
                continue
            out.append({col: (row[i] if i < len(row) else "") for i, col in enumerate(header)})
        return out

    def read_weeks(self, tabs, start_date, end_date):
        return {tab: self.read_week(tab, start_date, end_date) for tab in tabs}

    @staticmethod
    def _column_index(header, column, tab):
        try:
            return header.index(column)
        except ValueError:
            raise SheetReaderError(f"tab '{tab}' is missing the '{column}' column")

    def _assert_tab_exists(self, tab):
        if self._titles is None:
            meta = self.service.get(spreadsheetId=self.spreadsheet_id).execute()
            self._titles = {s["properties"]["title"] for s in meta.get("sheets", [])}
        if tab not in self._titles:
            raise SheetReaderError(f"configured rep_tab '{tab}' does not exist in the sheet")

    def _get_values(self, rng):
        resp = (
            self.service.values()
            .get(spreadsheetId=self.spreadsheet_id, range=rng)
            .execute()
        )
        return resp.get("values", [])
