"""Deduper: dedup by (date, lowercased prospect) within a batch and against the sheet
(contract 9, 10, 11, 18, 25)."""
from mastertracker.call_row_mapper import CallRowMapper
from mastertracker.deduper import Deduper
from tests.sample_calls import make_call


def _rows(*calls):
    mapper = CallRowMapper()
    return [mapper.to_row(c) for c in calls]


def test_same_date_same_prospect_collapses_to_one_row():
    # contract 9 - case-insensitive on prospect
    rows = _rows(
        make_call(id="a", date="2026-05-20", prospect="Jane Doe"),
        make_call(id="b", date="2026-05-20", prospect="jane doe"),
    )
    new = Deduper().new_rows(rows, existing_keys=set())
    assert len(new) == 1


def test_same_date_different_prospect_keeps_both():
    # contract 10
    rows = _rows(
        make_call(id="a", date="2026-05-20", prospect="Jane Doe"),
        make_call(id="b", date="2026-05-20", prospect="John Roe"),
    )
    new = Deduper().new_rows(rows, existing_keys=set())
    assert len(new) == 2


def test_different_date_same_prospect_keeps_both():
    # contract 11
    rows = _rows(
        make_call(id="a", date="2026-05-20", prospect="Jane Doe"),
        make_call(id="b", date="2026-05-21", prospect="Jane Doe"),
    )
    new = Deduper().new_rows(rows, existing_keys=set())
    assert len(new) == 2


def test_rows_already_present_in_the_sheet_are_dropped():
    # contract 18 - dedup decided from existing sheet keys, no local state involved
    existing = {("2026-05-20", "jane doe")}
    rows = _rows(make_call(id="a", date="2026-05-20", prospect="JANE DOE"))
    new = Deduper().new_rows(rows, existing_keys=existing)
    assert new == []
