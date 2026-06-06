"""SheetReader: week filtering, header normalization, and fail-fast on missing tab/column/date.

Driven through an injected fake Sheets service, so no network and no credentials.
"""
import datetime

import pytest

from weeklycheckin.sheet_reader import SheetReader, SheetReaderError

WEEK_START = datetime.date(2026, 5, 25)
WEEK_END = datetime.date(2026, 5, 31)

HEADER = ["Date", "Prospect", "Disposition", "Phone"]


class _FakeValues:
    def __init__(self, tabs_data):
        self._tabs_data = tabs_data
        self._range = None

    def get(self, spreadsheetId, range):
        self._range = range
        return self

    def execute(self):
        tab = self._range.split("!")[0]
        return {"values": self._tabs_data.get(tab, [])}


class FakeService:
    """Mirrors the spreadsheets() resource: ``get`` returns sheet metadata, ``values().get``
    returns a tab's rows."""

    def __init__(self, tabs_data, titles=None):
        self._tabs_data = tabs_data
        self._titles = list(tabs_data.keys()) if titles is None else titles
        self._meta = None

    def values(self):
        return _FakeValues(self._tabs_data)

    def get(self, spreadsheetId):
        self._meta = {"sheets": [{"properties": {"title": t}} for t in self._titles]}
        return self

    def execute(self):
        return self._meta


def _svc(rows, tab="Alice", titles=None):
    return FakeService({tab: [HEADER] + rows}, titles=titles)


def test_reads_only_rows_within_the_week():
    rows = [
        ["2026-05-25", "Jane", "Interested", "x"],
        ["2026-05-31", "John", "Meeting Booked", "y"],
        ["2026-06-01", "Late", "Interested", "z"],
        ["2026-05-24", "Early", "Interested", "w"],
    ]
    reader = SheetReader(_svc(rows), "sid")
    got = reader.read_week("Alice", WEEK_START, WEEK_END)
    assert [g["Prospect"] for g in got] == ["Jane", "John"]


def test_missing_tab_raises_with_tab_name():
    reader = SheetReader(_svc([], titles=["Other"]), "sid")
    with pytest.raises(SheetReaderError) as exc:
        reader.read_week("Alice", WEEK_START, WEEK_END)
    assert "Alice" in str(exc.value)


def test_non_iso_date_raises_with_the_offending_value():
    reader = SheetReader(_svc([["not-a-date", "Jane", "Interested", "x"]]), "sid")
    with pytest.raises(SheetReaderError) as exc:
        reader.read_week("Alice", WEEK_START, WEEK_END)
    assert "not-a-date" in str(exc.value)


def test_blank_date_rows_are_skipped():
    rows = [["", "Jane", "Interested", "x"], ["2026-05-26", "Bob", "Interested", "y"]]
    reader = SheetReader(_svc(rows), "sid")
    got = reader.read_week("Alice", WEEK_START, WEEK_END)
    assert [g["Prospect"] for g in got] == ["Bob"]


def test_blank_disposition_rows_are_skipped():
    rows = [["2026-05-26", "Jane", "", "x"], ["2026-05-27", "Bob", "Interested", "y"]]
    reader = SheetReader(_svc(rows), "sid")
    got = reader.read_week("Alice", WEEK_START, WEEK_END)
    assert [g["Prospect"] for g in got] == ["Bob"]


def test_header_whitespace_is_stripped_before_lookup():
    header = [" Date ", "Prospect", "Disposition "]
    svc = FakeService({"Alice": [header, ["2026-05-26", "Jane", "Interested"]]})
    reader = SheetReader(svc, "sid")
    got = reader.read_week("Alice", WEEK_START, WEEK_END)
    assert got[0]["Date"] == "2026-05-26"
    assert got[0]["Disposition"] == "Interested"


def test_missing_date_column_raises_with_column_name():
    svc = FakeService({"Alice": [["Prospect", "Disposition"], ["Jane", "Interested"]]})
    reader = SheetReader(svc, "sid")
    with pytest.raises(SheetReaderError) as exc:
        reader.read_week("Alice", WEEK_START, WEEK_END)
    assert "Date" in str(exc.value)


def test_missing_disposition_column_raises_with_column_name():
    svc = FakeService({"Alice": [["Date", "Prospect"], ["2026-05-26", "Jane"]]})
    reader = SheetReader(svc, "sid")
    with pytest.raises(SheetReaderError) as exc:
        reader.read_week("Alice", WEEK_START, WEEK_END)
    assert "Disposition" in str(exc.value)


def test_read_weeks_maps_each_tab():
    a = [["2026-05-26", "Jane", "Interested", "x"]]
    b = [["2026-05-27", "Bob", "Meeting Booked", "y"]]
    svc = FakeService({"Alice": [HEADER] + a, "Bob": [HEADER] + b})
    reader = SheetReader(svc, "sid")
    got = reader.read_weeks(["Alice", "Bob"], WEEK_START, WEEK_END)
    assert set(got.keys()) == {"Alice", "Bob"}
    assert got["Alice"][0]["Prospect"] == "Jane"
    assert got["Bob"][0]["Prospect"] == "Bob"
