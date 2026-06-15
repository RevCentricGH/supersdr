"""Pipeline ingest orchestration: the filter/dedup/mark-after-write rules wired together
(contract 5, 12, 13, 14, 15, 16, 17, 19, 23, 26)."""
from mastertracker.call_row_mapper import CallRowMapper, AUTO_COLUMNS
from mastertracker.deduper import Deduper
from mastertracker.disposition_filter import DispositionFilter
from mastertracker.ingest_state import IngestState
from mastertracker.pipeline import ingest_rep_calls
from tests.fakes import FakeSheet
from tests.sample_calls import make_call


def _deps(tmp_path, manual_columns=None):
    return dict(
        disposition_filter=DispositionFilter(["Interested", "Meeting Booked"], ["Callback"]),
        mapper=CallRowMapper(manual_columns=manual_columns or []),
        deduper=Deduper(),
        ingest_state=IngestState(str(tmp_path / "state.json")),
    )


def test_skipped_disposition_is_not_written_and_not_recorded(tmp_path):
    # contract 15, 23
    d = _deps(tmp_path)
    sheet = FakeSheet()
    calls = [make_call(id="c1", prospect="Skip Me", disposition="No Answer")]
    ingest_rep_calls(calls=calls, tab="Rep A", sheet=sheet, **d)
    assert sheet.prospects("Rep A") == []
    assert d["ingest_state"].is_ingested("c1") is False


def test_kept_disposition_is_written_and_recorded(tmp_path):
    # contract 13
    d = _deps(tmp_path)
    sheet = FakeSheet()
    calls = [make_call(id="c1", prospect="Jane Doe", disposition="Interested")]
    written = ingest_rep_calls(calls=calls, tab="Rep A", sheet=sheet, **d)
    assert written == 1
    assert sheet.prospects("Rep A") == ["Jane Doe"]
    assert d["ingest_state"].is_ingested("c1") is True


def test_call_is_not_marked_ingested_when_its_write_fails(tmp_path):
    # contract 14, 26 - c1 writes, c2 fails; only c1 is recorded
    d = _deps(tmp_path)
    sheet = FakeSheet(fail_on_call_id="c2")
    calls = [
        make_call(id="c1", prospect="Jane Doe", disposition="Interested"),
        make_call(id="c2", prospect="John Roe", disposition="Interested"),
    ]
    try:
        ingest_rep_calls(calls=calls, tab="Rep A", sheet=sheet, **d)
    except RuntimeError:
        pass
    assert d["ingest_state"].is_ingested("c1") is True
    assert d["ingest_state"].is_ingested("c2") is False


def test_calls_before_the_backfill_window_are_dropped(tmp_path):
    # contract 5
    d = _deps(tmp_path)
    sheet = FakeSheet()
    calls = [
        make_call(id="old", date="2026-01-01", prospect="Too Old", disposition="Interested"),
        make_call(id="new", date="2026-05-20", prospect="In Window", disposition="Interested"),
    ]
    ingest_rep_calls(
        calls=calls, tab="Rep A", sheet=sheet, backfill_start="2026-05-01", **d
    )
    assert sheet.prospects("Rep A") == ["In Window"]


def test_rerun_adds_no_duplicate_rows(tmp_path):
    # contract 17 - second run over the same calls writes nothing new
    d = _deps(tmp_path)
    sheet = FakeSheet()
    calls = [make_call(id="c1", prospect="Jane Doe", disposition="Interested")]
    ingest_rep_calls(calls=calls, tab="Rep A", sheet=sheet, **d)
    second = ingest_rep_calls(calls=calls, tab="Rep A", sheet=sheet, **d)
    assert second == 0
    assert sheet.prospects("Rep A") == ["Jane Doe"]


def test_rerun_with_empty_state_still_dedupes_against_the_sheet(tmp_path):
    # contract 18 - dedup must hold even when local state is wiped between runs
    d1 = _deps(tmp_path)
    sheet = FakeSheet()
    calls = [make_call(id="c1", prospect="Jane Doe", disposition="Interested")]
    ingest_rep_calls(calls=calls, tab="Rep A", sheet=sheet, **d1)

    d2 = _deps(tmp_path)  # fresh IngestState reading an empty/separate ledger
    d2["ingest_state"] = IngestState(str(tmp_path / "wiped.json"))
    second = ingest_rep_calls(calls=calls, tab="Rep A", sheet=sheet, **d2)
    assert second == 0
    assert sheet.prospects("Rep A") == ["Jane Doe"]


def test_manual_column_value_survives_a_rerun(tmp_path):
    # contract 12, 19 - an operator's manual cell is never clobbered
    d = _deps(tmp_path, manual_columns=["Notes"])
    header = AUTO_COLUMNS + ["Notes"]
    sheet = FakeSheet()
    sheet.seed_row(
        "Rep A",
        header,
        {"Date": "2026-05-20", "Prospect": "Jane Doe", "Disposition": "Interested",
         "Phone": "", "Duration (sec)": "", "Call ID": "c1", "Recording URL": "",
         "Notes": "called back, hot lead"},
    )
    calls = [make_call(id="c1", date="2026-05-20", prospect="Jane Doe", disposition="Interested")]
    ingest_rep_calls(calls=calls, tab="Rep A", sheet=sheet, **d)
    rows = sheet.tabs["Rep A"]["rows"]
    assert len(rows) == 1
    assert rows[0]["Notes"] == "called back, hot lead"


def test_disposition_tagged_after_first_run_is_picked_up_later(tmp_path):
    # contract 16 - same call id, untagged then tagged
    d = _deps(tmp_path)
    sheet = FakeSheet()
    untagged = [make_call(id="c1", prospect="Jane Doe", disposition="No Answer")]
    ingest_rep_calls(calls=untagged, tab="Rep A", sheet=sheet, **d)
    assert sheet.prospects("Rep A") == []

    tagged = [make_call(id="c1", prospect="Jane Doe", disposition="Interested")]
    ingest_rep_calls(calls=tagged, tab="Rep A", sheet=sheet, **d)
    assert sheet.prospects("Rep A") == ["Jane Doe"]
