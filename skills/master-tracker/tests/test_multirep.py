"""Multi-rep routing: each rep's calls land only in that rep's tab (contract 20, 21, 27)."""
from mastertracker.ingest_state import IngestState
from mastertracker.pipeline import run
from tests.fakes import FakeApollo, FakeSheet
from tests.sample_calls import make_call


def _config(reps):
    return {
        "reps": reps,
        "keep_dispositions": ["Interested"],
        "keep_prefixes": [],
        "manual_columns": ["Notes"],
    }


def test_single_rep_runs_without_error(tmp_path):
    # contract 20
    apollo = FakeApollo({"u1": [make_call(id="c1", prospect="Jane Doe", disposition="Interested")]})
    sheet = FakeSheet()
    state = IngestState(str(tmp_path / "state.json"))
    config = _config({"Alice": {"apollo_user_id": "u1"}})

    results = run(config, apollo=apollo, sheet=sheet, ingest_state=state)
    assert results == {"Alice": 1}
    assert sheet.prospects("Alice") == ["Jane Doe"]


def test_two_reps_route_to_separate_tabs(tmp_path):
    # contract 21, 27 - each rep's prospect appears only in that rep's tab
    apollo = FakeApollo(
        {
            "u1": [make_call(id="a1", prospect="Alice Prospect", disposition="Interested")],
            "u2": [make_call(id="b1", prospect="Bob Prospect", disposition="Interested")],
        }
    )
    sheet = FakeSheet()
    state = IngestState(str(tmp_path / "state.json"))
    config = _config({"Alice": {"apollo_user_id": "u1"}, "Bob": {"apollo_user_id": "u2"}})

    run(config, apollo=apollo, sheet=sheet, ingest_state=state)

    assert sheet.prospects("Alice") == ["Alice Prospect"]
    assert sheet.prospects("Bob") == ["Bob Prospect"]
    assert "Bob Prospect" not in sheet.prospects("Alice")
    assert "Alice Prospect" not in sheet.prospects("Bob")


def test_state_is_persisted_when_a_rep_write_fails_midway(tmp_path):
    # run() must save the ledger even if a mid-rep write raises, so rows written before the
    # failure (c1) survive to disk and are not re-fetched next run; the failing call (c2) stays out
    apollo = FakeApollo(
        {
            "u1": [
                make_call(id="c1", prospect="Jane Doe", disposition="Interested"),
                make_call(id="c2", prospect="John Roe", disposition="Interested"),
            ]
        }
    )
    sheet = FakeSheet(fail_on_call_id="c2")
    path = str(tmp_path / "state.json")
    config = _config({"Alice": {"apollo_user_id": "u1"}})

    try:
        run(config, apollo=apollo, sheet=sheet, ingest_state=IngestState(path))
    except RuntimeError:
        pass

    reloaded = IngestState(path)  # read from disk: proves save() ran despite the failure
    assert reloaded.is_ingested("c1") is True
    assert reloaded.is_ingested("c2") is False
