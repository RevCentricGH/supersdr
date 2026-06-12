"""SmartLeadClient: backoff, timeout, normalization, and the closed-default date-range check.

Driven through an injected fake transport and a fake sleep, so no network and no real waits.
"""
import pytest

from weeklycheckin.smartlead_client import (
    SmartLeadAPIError,
    SmartLeadClient,
    StatsResolutionError,
)

START = "2026-05-25"
END = "2026-05-31"


class FakeResponse:
    def __init__(self, status_code, payload=None, headers=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.headers = headers or {}

    def json(self):
        return self._payload


class FakeTransport:
    """Pops a queued response per request, or raises a preset exception to model a timeout."""

    def __init__(self, responses, raise_exc=None):
        self._responses = list(responses)
        self.raise_exc = raise_exc
        self.calls = []

    def __call__(self, method, url, params, timeout):
        self.calls.append({"method": method, "url": url, "params": params, "timeout": timeout})
        if self.raise_exc is not None:
            raise self.raise_exc
        return self._responses.pop(0)


def _ok_stats(start=START, end=END):
    return {
        "start_date": start,
        "end_date": end,
        "sent_count": 100,
        "open_count": 40,
        "reply_count": 10,
        "bounce_count": 2,
    }


def _client(transport, **kw):
    return SmartLeadClient("key", transport=transport, sleep=lambda s: None, **kw)


def test_success_returns_normalized_stats_with_rates():
    transport = FakeTransport([FakeResponse(200, _ok_stats())])
    stats = _client(transport).campaign_stats(123, START, END)
    assert stats == {
        "opens": 40,
        "replies": 10,
        "bounces": 2,
        "sent": 100,
        "open_rate": 0.4,
        "reply_rate": 0.1,
    }
    # auth is the api_key query param, never hardcoded into the URL
    assert transport.calls[0]["params"]["api_key"] == "key"
    assert transport.calls[0]["params"]["start_date"] == START


def test_429_then_success_retries_with_backoff():
    transport = FakeTransport(
        [FakeResponse(429, headers={"Retry-After": "2"}), FakeResponse(200, _ok_stats())]
    )
    slept = []
    client = SmartLeadClient("key", transport=transport, sleep=lambda s: slept.append(s))
    stats = client.campaign_stats(1, START, END)
    assert stats["sent"] == 100
    assert slept == [2.0]


def test_429_exhausts_retries_and_raises():
    transport = FakeTransport([FakeResponse(429) for _ in range(10)])
    slept = []
    client = SmartLeadClient(
        "key", transport=transport, sleep=lambda s: slept.append(s), max_retries=5
    )
    with pytest.raises(SmartLeadAPIError):
        client.campaign_stats(1, START, END)
    assert len(slept) == 5  # 5 retries, then give up


def test_non_200_raises():
    with pytest.raises(SmartLeadAPIError):
        _client(FakeTransport([FakeResponse(500)])).campaign_stats(1, START, END)


def test_transport_timeout_raises_api_error():
    transport = FakeTransport([], raise_exc=TimeoutError("timed out"))
    with pytest.raises(SmartLeadAPIError):
        _client(transport).campaign_stats(1, START, END)


def test_thirty_second_timeout_is_passed_to_the_transport():
    transport = FakeTransport([FakeResponse(200, _ok_stats())])
    _client(transport).campaign_stats(1, START, END)
    assert transport.calls[0]["timeout"] == 30


def test_missing_breakdown_and_echo_raises_resolution_error():
    payload = {"sent_count": 100, "open_count": 40, "reply_count": 10, "bounce_count": 2}
    with pytest.raises(StatsResolutionError):
        _client(FakeTransport([FakeResponse(200, payload)])).campaign_stats(1, START, END)


def test_mismatched_date_echo_raises_resolution_error():
    payload = _ok_stats(start="2026-01-01", end="2026-01-07")
    with pytest.raises(StatsResolutionError):
        _client(FakeTransport([FakeResponse(200, payload)])).campaign_stats(1, START, END)


def test_per_day_breakdown_is_accepted():
    payload = {
        "by_date": [
            {"date": "2026-05-25", "sent_count": 50},
            {"date": "2026-05-26", "sent_count": 50},
        ],
        "sent_count": 100,
        "open_count": 40,
        "reply_count": 10,
        "bounce_count": 2,
    }
    stats = _client(FakeTransport([FakeResponse(200, payload)])).campaign_stats(1, START, END)
    assert stats["sent"] == 100


def test_zero_sent_yields_zero_rates_not_crash():
    payload = _ok_stats()
    payload.update(sent_count=0, open_count=0, reply_count=0, bounce_count=0)
    stats = _client(FakeTransport([FakeResponse(200, payload)])).campaign_stats(1, START, END)
    assert stats["open_rate"] == 0.0
    assert stats["reply_rate"] == 0.0


def test_empty_response_returns_none():
    stats = _client(FakeTransport([FakeResponse(200, {})])).campaign_stats(1, START, END)
    assert stats is None


def test_fetch_campaign_stats_warns_and_omits_empty(capsys):
    transport = FakeTransport([FakeResponse(200, _ok_stats()), FakeResponse(200, {})])
    out = _client(transport).fetch_campaign_stats([1, 2], START, END)
    assert set(out.keys()) == {1}
    err = capsys.readouterr().err
    assert "2" in err
