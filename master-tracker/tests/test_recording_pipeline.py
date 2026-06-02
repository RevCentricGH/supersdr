"""RecordingSource wired into the pipeline: the recording-link column is the source's sole
authority, and an unselected / non-resolving / raising / unknown source degrades gracefully
(contract 9, 10, 11, 12, 13).
"""
from mastertracker.call_row_mapper import AUTO_COLUMNS, CallRowMapper
from mastertracker.deduper import Deduper
from mastertracker.disposition_filter import DispositionFilter
from mastertracker.ingest_state import IngestState
from mastertracker.pipeline import ingest_rep_calls, run
from mastertracker.recording_source import RecordingSource, UnknownRecordingSource
from tests.fakes import FakeApollo, FakeSheet
from tests.sample_calls import make_call

REC = "Recording URL"


def _deps(tmp_path, manual_columns=None):
    return dict(
        disposition_filter=DispositionFilter(["Interested"], []),
        mapper=CallRowMapper(manual_columns=manual_columns or []),
        deduper=Deduper(),
        ingest_state=IngestState(str(tmp_path / "state.json")),
    )


def _rec(sheet, tab, prospect):
    for row in sheet.tabs.get(tab, {}).get("rows", []):
        if row.get("Prospect") == prospect:
            return row.get(REC)
    raise AssertionError(f"no row for {prospect} in {tab}")


class _ApolloLike(RecordingSource):
    def resolve(self, call):
        return call.get("recording_url") or ""


class _RaisingSource(RecordingSource):
    def resolve(self, call):
        raise RuntimeError("dialer API down")


# --- contract 9: a resolved link populates the column -------------------------------

def test_resolved_link_is_written_to_the_recording_column(tmp_path):
    sheet = FakeSheet()
    calls = [make_call(id="c1", prospect="Jane Doe", disposition="Interested",
                       recording_url="https://app.apollo.io/calls/c1/rec.mp3")]
    ingest_rep_calls(calls=calls, tab="Rep A", sheet=sheet,
                     recording_source=_ApolloLike(), **_deps(tmp_path))
    assert _rec(sheet, "Rep A", "Jane Doe") == "https://app.apollo.io/calls/c1/rec.mp3"


# --- contract 11: no source -> column blank, no crash -------------------------------

def test_no_source_leaves_the_column_blank_even_when_the_call_carries_a_url(tmp_path):
    # the source is the sole authority: with none configured the column is blank
    sheet = FakeSheet()
    calls = [make_call(id="c1", prospect="Jane Doe", disposition="Interested",
                       recording_url="https://app.apollo.io/calls/c1/rec.mp3")]
    ingest_rep_calls(calls=calls, tab="Rep A", sheet=sheet, recording_source=None, **_deps(tmp_path))
    assert _rec(sheet, "Rep A", "Jane Doe") == ""


# --- contract 12: source cannot resolve / raises -> blank, no crash -----------------

def test_unresolved_call_leaves_the_column_blank(tmp_path):
    sheet = FakeSheet()
    calls = [make_call(id="c1", prospect="Jane Doe", disposition="Interested", recording_url="")]
    ingest_rep_calls(calls=calls, tab="Rep A", sheet=sheet,
                     recording_source=_ApolloLike(), **_deps(tmp_path))
    assert _rec(sheet, "Rep A", "Jane Doe") == ""


def test_a_source_that_raises_does_not_crash_the_run_and_leaves_blank(tmp_path):
    sheet = FakeSheet()
    calls = [make_call(id="c1", prospect="Jane Doe", disposition="Interested")]
    written = ingest_rep_calls(calls=calls, tab="Rep A", sheet=sheet,
                               recording_source=_RaisingSource(), **_deps(tmp_path))
    assert written == 1  # the row is still written
    assert _rec(sheet, "Rep A", "Jane Doe") == ""


# --- contract 13: unknown source -> clear error at startup, not at resolve time -----

def test_unknown_source_raises_at_startup_before_any_row_is_written(tmp_path):
    apollo = FakeApollo({"u1": [make_call(id="c1", prospect="Jane Doe", disposition="Interested")]})
    sheet = FakeSheet()
    state = IngestState(str(tmp_path / "state.json"))
    config = {
        "reps": {"Rep A": {"apollo_user_id": "u1"}},
        "keep_dispositions": ["Interested"],
        "recording_source": {"type": "bogus"},
    }
    try:
        run(config, apollo=apollo, sheet=sheet, ingest_state=state)
        assert False, "expected UnknownRecordingSource"
    except UnknownRecordingSource:
        pass
    assert sheet.tabs.get("Rep A", {}).get("rows", []) == []  # nothing written at resolve time


# --- contract 10: per-adapter integration through run() -----------------------------

def _run_adapter(tmp_path, name, source_cfg, resolvable_call, unresolvable_call):
    apollo = FakeApollo({"u1": [resolvable_call, unresolvable_call]})
    sheet = FakeSheet()
    state = IngestState(str(tmp_path / f"{name}_state.json"))
    config = {
        "reps": {"Rep A": {"apollo_user_id": "u1"}},
        "keep_dispositions": ["Interested"],
        "manual_columns": ["Notes"],
        "recording_source": source_cfg,
    }
    run(config, apollo=apollo, sheet=sheet, ingest_state=state)
    return sheet


def test_each_adapter_resolves_its_own_distinct_link_and_degrades_when_it_cannot(tmp_path):
    # contract 10 - select each adapter by config; the column goes blank -> adapter-specific
    # value for the resolvable call and stays blank for the unresolvable one; the three
    # resolved links are genuinely different.
    apollo_sheet = _run_adapter(
        tmp_path, "apollo",
        {"type": "apollo"},
        make_call(id="a1", prospect="Apollo Yes", disposition="Interested",
                  recording_url="https://app.apollo.io/calls/a1/rec.mp3"),
        make_call(id="a2", prospect="Apollo No", disposition="Interested", recording_url=""),
    )
    trellus_sheet = _run_adapter(
        tmp_path, "trellus",
        {"type": "trellus"},
        make_call(id="t1", prospect="Trellus Yes", disposition="Interested",
                  note="Trellus session sess_ab12cd34 logged"),
        make_call(id="t2", prospect="Trellus No", disposition="Interested", note="no answer"),
    )
    manual_sheet = _run_adapter(
        tmp_path, "manual",
        {"type": "manual-url"},
        {**make_call(id="m1", prospect="Manual Yes", disposition="Interested"),
         "manual_recording_url": "https://drive.google.com/file/d/m1/view"},
        make_call(id="m2", prospect="Manual No", disposition="Interested"),
    )

    apollo_link = _rec(apollo_sheet, "Rep A", "Apollo Yes")
    trellus_link = _rec(trellus_sheet, "Rep A", "Trellus Yes")
    manual_link = _rec(manual_sheet, "Rep A", "Manual Yes")

    # (a)/(b)/(c): each resolvable call's column is populated with an adapter-specific link
    assert apollo_link == "https://app.apollo.io/calls/a1/rec.mp3"
    assert trellus_link == "https://app.trellus.ai/recordings/sess_ab12cd34"
    assert manual_link == "https://drive.google.com/file/d/m1/view"
    # passing all three requires three genuinely different resolved links
    assert len({apollo_link, trellus_link, manual_link}) == 3

    # (d): the unresolvable call per adapter leaves the column blank, no exception
    assert _rec(apollo_sheet, "Rep A", "Apollo No") == ""
    assert _rec(trellus_sheet, "Rep A", "Trellus No") == ""
    assert _rec(manual_sheet, "Rep A", "Manual No") == ""
