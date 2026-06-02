"""ApolloClient: paged search, 429-aware backoff, backfill bounding (contract 3, 4, 5).

Driven through an injected fake transport and a fake sleep, so no network and no real waits.
"""
import pytest

from mastertracker.apollo_client import ApolloClient, ApolloError


class FakeResponse:
    def __init__(self, status_code, payload=None, headers=None):
        self.status_code = status_code
        self._payload = payload or {}
        self.headers = headers or {}

    def json(self):
        return self._payload


class FakeTransport:
    """Pops a queued response per request and records the request payloads."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.requests = []

    def __call__(self, method, url, headers, json):
        self.requests.append({"method": method, "url": url, "headers": headers, "json": json})
        return self._responses.pop(0)


def _raw(id, date, prospect, disposition="Interested"):
    return {
        "id": id,
        "created_at": date + "T15:04:05Z",
        "contact": {"name": prospect},
        "disposition": disposition,
        "phone_number": "+15550000000",
        "duration": 60,
    }


def test_search_fetches_every_page_for_the_rep():
    # contract 3 - two pages, both fetched and concatenated
    transport = FakeTransport([
        FakeResponse(200, {"phone_calls": [_raw("a", "2026-05-20", "Jane Doe"),
                                           _raw("b", "2026-05-20", "John Roe")],
                           "pagination": {"page": 1, "total_pages": 2}}),
        FakeResponse(200, {"phone_calls": [_raw("c", "2026-05-21", "Sam Poe")],
                           "pagination": {"page": 2, "total_pages": 2}}),
    ])
    client = ApolloClient("key", transport=transport, sleep=lambda s: None)
    calls = client.search_calls({"apollo_user_id": "u1"})
    assert [c["id"] for c in calls] == ["a", "b", "c"]
    assert len(transport.requests) == 2


def test_retries_after_a_429_with_backoff():
    # contract 4 - a 429 is retried, not fatal; sleep is invoked before the retry
    slept = []
    transport = FakeTransport([
        FakeResponse(429, headers={"Retry-After": "2"}),
        FakeResponse(200, {"phone_calls": [_raw("a", "2026-05-20", "Jane Doe")],
                           "pagination": {"page": 1, "total_pages": 1}}),
    ])
    client = ApolloClient("key", transport=transport, sleep=lambda s: slept.append(s))
    calls = client.search_calls({"apollo_user_id": "u1"})
    assert [c["id"] for c in calls] == ["a"]
    assert slept == [2.0]


def test_bounds_results_to_the_backfill_window():
    # contract 5 - the since date is sent to Apollo and pre-window records are dropped locally
    transport = FakeTransport([
        FakeResponse(200, {"phone_calls": [_raw("old", "2026-01-01", "Too Old"),
                                           _raw("new", "2026-05-20", "In Window")],
                           "pagination": {"page": 1, "total_pages": 1}}),
    ])
    client = ApolloClient("key", transport=transport, sleep=lambda s: None)
    calls = client.search_calls({"apollo_user_id": "u1"}, since="2026-05-01")
    assert [c["id"] for c in calls] == ["new"]
    # the window is also pushed to the server, not just filtered after the fact
    sent = transport.requests[0]["json"]
    assert "2026-05-01" in str(sent)


def test_normalizes_raw_apollo_fields():
    transport = FakeTransport([
        FakeResponse(200, {"phone_calls": [_raw("a", "2026-05-20", "Jane Doe", "Meeting Booked")],
                           "pagination": {"page": 1, "total_pages": 1}}),
    ])
    client = ApolloClient("key", transport=transport, sleep=lambda s: None)
    call = client.search_calls({"apollo_user_id": "u1"})[0]
    assert call["date"] == "2026-05-20"
    assert call["prospect"] == "Jane Doe"
    assert call["disposition"] == "Meeting Booked"


def test_normalizes_the_call_note_so_the_trellus_source_can_parse_it():
    # the trellus RecordingSource parses a session id out of the note; the note must survive
    # normalization for that to work on real Apollo data
    raw = _raw("a", "2026-05-20", "Jane Doe")
    raw["note"] = "Trellus session sess_ab12cd34"
    transport = FakeTransport([
        FakeResponse(200, {"phone_calls": [raw], "pagination": {"page": 1, "total_pages": 1}}),
    ])
    client = ApolloClient("key", transport=transport, sleep=lambda s: None)
    call = client.search_calls({"apollo_user_id": "u1"})[0]
    assert call["note"] == "Trellus session sess_ab12cd34"


def test_normalize_defaults_absent_duration_to_zero():
    # both duration fields absent -> a numeric 0, never None, so the sheet column stays
    # all-numeric and downstream formulas do not choke on a JSON null
    call = ApolloClient._normalize({"id": "x", "created_at": "2026-05-20T00:00:00Z"})
    assert call["duration_sec"] == 0
    assert call["duration_sec"] is not None


def test_search_refuses_a_rep_with_no_user_id():
    # regression: an empty apollo_user_id must not fall through to querying all users
    client = ApolloClient("key", transport=FakeTransport([]), sleep=lambda s: None)
    with pytest.raises(ApolloError):
        client.search_calls({"apollo_user_id": ""})
