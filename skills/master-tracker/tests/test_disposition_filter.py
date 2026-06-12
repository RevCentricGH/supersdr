"""DispositionFilter: pure keep-set + prefix match (contract 6, 7, 8, 22)."""
from mastertracker.disposition_filter import DispositionFilter
from tests.sample_calls import make_call


def _filter():
    return DispositionFilter(
        keep_dispositions=["Interested", "Meeting Booked"],
        keep_prefixes=["Callback"],
    )


def test_keeps_call_with_disposition_in_keep_list():
    # contract 6
    call = make_call(disposition="Interested")
    assert _filter().keep(call["disposition"]) is True


def test_skips_call_whose_disposition_is_not_kept_and_matches_no_prefix():
    # contract 7 - decided purely from the record, no API call needed
    call = make_call(disposition="No Answer")
    assert _filter().keep(call["disposition"]) is False


def test_keeps_call_whose_disposition_starts_with_a_kept_prefix():
    # contract 8
    call = make_call(disposition="Callback - next week")
    assert _filter().keep(call["disposition"]) is True


def test_keep_is_case_insensitive():
    call = make_call(disposition="interested")
    assert _filter().keep(call["disposition"]) is True


def test_missing_disposition_is_skipped():
    assert _filter().keep(None) is False
    assert _filter().keep("") is False
