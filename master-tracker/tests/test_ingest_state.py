"""IngestState: the ingested-call ledger persisted to state.json (contract 13, 14, 26)."""
from mastertracker.ingest_state import IngestState


def test_unknown_call_is_not_ingested(tmp_path):
    state = IngestState(str(tmp_path / "state.json"))
    assert state.is_ingested("call_1") is False


def test_mark_then_persist_roundtrips(tmp_path):
    path = str(tmp_path / "state.json")
    state = IngestState(path)
    state.mark_ingested("call_1")
    state.save()

    reloaded = IngestState(path)
    assert reloaded.is_ingested("call_1") is True
    assert reloaded.is_ingested("call_2") is False


def test_absent_state_file_loads_as_empty(tmp_path):
    # contract 18 leans on this - a missing ledger must not error and must ingest nothing
    state = IngestState(str(tmp_path / "missing.json"))
    assert state.is_ingested("anything") is False


def test_marking_is_only_durable_after_save(tmp_path):
    # the mark-after-write invariant relies on save() being the commit point
    path = str(tmp_path / "state.json")
    state = IngestState(path)
    state.mark_ingested("call_1")
    # not saved yet -> a fresh reader sees nothing
    assert IngestState(path).is_ingested("call_1") is False
    state.save()
    assert IngestState(path).is_ingested("call_1") is True
