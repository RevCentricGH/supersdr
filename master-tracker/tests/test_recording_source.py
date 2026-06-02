"""RecordingSource adapters: resolve a recording link from a normalized call record.

The dialer is abstracted behind one interface so callers never branch on dialer
(contract 1-8, 13). Each adapter resolves from a fixture call record; an unresolvable or
malformed record yields a blank string without raising.
"""
from mastertracker.recording_source import (
    ApolloRecordingSource,
    ManualUrlRecordingSource,
    RecordingSource,
    TrellusRecordingSource,
    UnknownRecordingSource,
    build_recording_source,
    safe_resolve,
)
from tests.sample_calls import make_call


# --- Apollo adapter (contract 2, 6) -------------------------------------------------

def test_apollo_resolves_the_recording_url_apollo_attached_to_the_call():
    # contract 6 - a non-empty, apollo-specific link that includes the call's identifier
    call = make_call(
        id="call_apollo_1",
        recording_url="https://app.apollo.io/calls/call_apollo_1/recording.mp3",
    )
    link = ApolloRecordingSource().resolve(call)
    assert link == "https://app.apollo.io/calls/call_apollo_1/recording.mp3"
    assert "apollo" in link and "call_apollo_1" in link


def test_apollo_returns_blank_when_the_call_has_no_recording_url():
    # contract 6 - nothing to resolve
    assert ApolloRecordingSource().resolve(make_call(recording_url="")) == ""


def test_apollo_returns_blank_without_raising_on_a_malformed_call_record():
    # contract 6 - missing required fields / wrong types must not crash
    source = ApolloRecordingSource()
    assert source.resolve({}) == ""  # missing recording_url entirely
    assert source.resolve({"recording_url": None}) == ""
    assert source.resolve({"recording_url": 12345}) == ""  # wrong type
    assert source.resolve({"recording_url": "not-a-url"}) == ""  # no scheme
    assert source.resolve(None) == ""  # not even a dict


# --- Trellus adapter (contract 3, 7) ------------------------------------------------

def test_trellus_parses_the_session_id_from_the_note_and_builds_the_link():
    # contract 3, 7 - a trellus-specific link containing the parsed session id
    call = make_call(note="Dialed via Trellus. session sess_ab12cd34 logged.")
    link = TrellusRecordingSource().resolve(call)
    assert link == "https://app.trellus.ai/recordings/sess_ab12cd34"
    assert "trellus" in link and "sess_ab12cd34" in link


def test_trellus_returns_blank_when_the_note_has_no_session_id():
    # contract 7 - no session id in the note
    assert TrellusRecordingSource().resolve(make_call(note="Left a voicemail, no answer.")) == ""


def test_trellus_returns_blank_without_raising_on_a_malformed_session_id():
    # contract 7 - a partial / corrupt token must not resolve and must not crash
    source = TrellusRecordingSource()
    assert source.resolve(make_call(note="Trellus session sess_ab12 (partial)")) == ""  # too short
    assert source.resolve(make_call(note="session id: sess_ corrupt")) == ""  # empty token
    assert source.resolve(make_call(note="sessab12cd34 missing underscore")) == ""  # wrong format
    assert source.resolve({"note": None}) == ""  # wrong type
    assert source.resolve({}) == ""  # missing note
    assert source.resolve(None) == ""  # not even a dict


# --- manual-url adapter (contract 4, 8) ---------------------------------------------

def _manual_call(url, **kw):
    return {**make_call(**kw), "manual_recording_url": url}


def test_manual_url_returns_the_attached_url_exactly():
    # contract 8 - a URL the operator pasted is returned unchanged
    call = _manual_call("https://drive.google.com/file/d/manual_rec_1/view")
    assert ManualUrlRecordingSource().resolve(call) == "https://drive.google.com/file/d/manual_rec_1/view"


def test_manual_url_returns_blank_when_no_url_is_attached():
    # contract 8 - field absent / empty
    assert ManualUrlRecordingSource().resolve(make_call()) == ""
    assert ManualUrlRecordingSource().resolve(_manual_call("")) == ""


def test_manual_url_returns_blank_without_raising_on_a_malformed_value():
    # contract 8 - a non-URL value must not resolve and must not crash
    source = ManualUrlRecordingSource()
    assert source.resolve(_manual_call("recording pending")) == ""  # no scheme
    assert source.resolve(_manual_call("file.mp3")) == ""  # no scheme
    assert source.resolve({"manual_recording_url": 99}) == ""  # wrong type
    assert source.resolve(None) == ""  # not even a dict


# --- the config-driven factory (contract 2, 3, 4, 5, 11, 13) ------------------------

def test_factory_selects_the_adapter_named_in_config():
    # contract 2, 3, 4, 5 - the source in use is determined by config, not hardcoded
    assert isinstance(build_recording_source({"recording_source": {"type": "apollo"}}), ApolloRecordingSource)
    assert isinstance(build_recording_source({"recording_source": {"type": "trellus"}}), TrellusRecordingSource)
    assert isinstance(build_recording_source({"recording_source": {"type": "manual-url"}}), ManualUrlRecordingSource)


def test_factory_passes_per_adapter_config_through():
    # contract 5 - trellus base_url and manual field overrides are honored
    trellus = build_recording_source(
        {"recording_source": {"type": "trellus", "base_url": "https://my.trellus.example/rec"}}
    )
    assert trellus.resolve(make_call(note="sess_ab12cd34")) == "https://my.trellus.example/rec/sess_ab12cd34"
    manual = build_recording_source({"recording_source": {"type": "manual-url", "field": "rec_link"}})
    assert manual.resolve({"rec_link": "https://x.test/r"}) == "https://x.test/r"


def test_factory_returns_none_when_no_source_is_configured():
    # contract 11 - absent or null config means no source (caller leaves the column blank)
    assert build_recording_source({}) is None
    assert build_recording_source({"recording_source": None}) is None
    assert build_recording_source({"recording_source": {"type": ""}}) is None


def test_factory_raises_a_clear_error_for_an_unknown_source_name():
    # contract 13 - a typo'd source is caught at startup, not silently swallowed
    try:
        build_recording_source({"recording_source": {"type": "bogus"}})
        assert False, "expected UnknownRecordingSource"
    except UnknownRecordingSource as err:
        msg = str(err)
        assert "bogus" in msg
        assert "apollo" in msg and "trellus" in msg and "manual-url" in msg


# --- safe_resolve degradation guard (contract 12) -----------------------------------

class _RaisingSource(RecordingSource):
    def resolve(self, call):
        raise RuntimeError("boom")


class _NoneSource(RecordingSource):
    def resolve(self, call):
        return None


def test_safe_resolve_returns_blank_when_there_is_no_source():
    # contract 11/12 - a None source never crashes the caller
    assert safe_resolve(None, make_call()) == ""


def test_safe_resolve_swallows_an_adapter_that_raises():
    # contract 12 - even a buggy adapter degrades to blank, not a crash
    assert safe_resolve(_RaisingSource(), make_call()) == ""


def test_safe_resolve_normalizes_a_none_or_whitespace_result_to_blank():
    # contract 12 - a source that returns nothing useful leaves the column blank
    assert safe_resolve(_NoneSource(), make_call()) == ""


def test_safe_resolve_returns_the_resolved_link_when_one_is_found():
    # contract 9 - a resolved link is passed through (stripped)
    call = make_call(recording_url="https://app.apollo.io/calls/c1/rec.mp3")
    assert safe_resolve(ApolloRecordingSource(), call) == "https://app.apollo.io/calls/c1/rec.mp3"
