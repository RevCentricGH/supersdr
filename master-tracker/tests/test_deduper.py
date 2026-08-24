"""Deduper: call ID is the primary identity, (date, lowercased prospect) the secondary,
decided against the sheet; a same-day, same-disposition duplicate pair keeps the row
with a recording (contract 9, 10, 11, 18, 25)."""
from mastertracker.call_row_mapper import RECORDING_COLUMN, CallRowMapper
from mastertracker.deduper import Deduper
from tests.sample_calls import make_call


def _rows(*calls):
    # Mirrors the pipeline: the recording is resolved onto the row before dedup.
    mapper = CallRowMapper()
    rows = []
    for call in calls:
        row = mapper.to_row(call)
        row.values[RECORDING_COLUMN] = call.get("recording_url") or ""
        rows.append(row)
    return rows


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


def test_same_call_id_twice_in_a_batch_collapses_to_one_row():
    # paging overlap can yield the same call twice; the ID is the primary identity
    rows = _rows(
        make_call(id="a", date="2026-05-20", prospect="Jane Doe"),
        make_call(id="a", date="2026-05-21", prospect="Jane Doe"),
    )
    new = Deduper().new_rows(rows, existing_keys=set())
    assert len(new) == 1


def test_same_day_duplicate_keeps_the_row_with_the_recording():
    # double-logged conversation: recording-less row first, recorded row second
    rows = _rows(
        make_call(id="a", date="2026-05-20", prospect="Jane Doe"),
        make_call(
            id="b", date="2026-05-20", prospect="Jane Doe",
            recording_url="https://rec.example/b",
        ),
    )
    new = Deduper().new_rows(rows, existing_keys=set())
    assert len(new) == 1
    assert new[0].call_id == "b"
    assert new[0].has_recording


def test_same_day_duplicate_recorded_row_first_still_wins():
    rows = _rows(
        make_call(
            id="a", date="2026-05-20", prospect="Jane Doe",
            recording_url="https://rec.example/a",
        ),
        make_call(id="b", date="2026-05-20", prospect="Jane Doe"),
    )
    new = Deduper().new_rows(rows, existing_keys=set())
    assert len(new) == 1
    assert new[0].call_id == "a"


def test_recorded_row_with_a_different_disposition_does_not_replace_the_first():
    # two genuinely different conversations in one day: a recorded afternoon follow-up
    # must never replace the morning's booked meeting in the sheet
    rows = _rows(
        make_call(id="a", date="2026-05-20", prospect="Jane Doe",
                  disposition="Meeting Booked"),
        make_call(id="b", date="2026-05-20", prospect="Jane Doe",
                  disposition="Interested", recording_url="https://rec.example/b"),
    )
    new = Deduper().new_rows(rows, existing_keys=set())
    assert len(new) == 1
    assert new[0].call_id == "a"
    assert new[0].disposition == "Meeting Booked"


def test_re_returned_copy_of_the_same_call_contributes_its_recording():
    # paging re-returns the same call after its recording attached mid-run: the
    # recorded copy wins even though the ID was already seen
    rows = _rows(
        make_call(id="a", date="2026-05-20", prospect="Jane Doe"),
        make_call(id="a", date="2026-05-20", prospect="Jane Doe",
                  recording_url="https://rec.example/a"),
    )
    new = Deduper().new_rows(rows, existing_keys=set())
    assert len(new) == 1
    assert new[0].has_recording
