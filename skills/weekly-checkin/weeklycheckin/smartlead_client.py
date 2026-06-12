"""SmartLeadClient - per-campaign stats with 429-aware backoff and a closed-default date check.

A thin wrapper over the SmartLead REST API. Auth is the ``api_key`` query param on every
request (mirrors master-tracker's ApolloClient injection pattern: the transport and sleep are
injectable so the behavior can be exercised without a network or real waits). The raw response
is flattened in ``_normalize`` to one stable shape:

    {"opens": int, "replies": int, "bounces": int, "sent": int,
     "open_rate": float, "reply_rate": float}

Rates are count / sent, defaulting to 0.0 when sent is 0 (no ZeroDivisionError on an empty week).

It fails closed on date-range uncertainty: SmartLead's /statistics endpoint may return lifetime
aggregates rather than figures scoped to the requested range. ``campaign_stats`` raises
``StatsResolutionError`` unless the response carries a per-day breakdown or echoes back
``start_date``/``end_date`` matching the requested range, so weekly stats are omitted rather than
silently mislabeled as lifetime totals. A campaign the API has no data for returns ``None`` (the
caller warns and omits it); the network errors (429 retry exhaustion, timeout, non-2xx) raise
``SmartLeadAPIError``.
"""
import sys

CAMPAIGNS_PATH = "/api/v1/campaigns"
# Response keys that count as a genuine per-day breakdown of the requested range.
PER_DAY_KEYS = ("by_date", "daily", "per_day", "days")


class SmartLeadClient:
    def __init__(
        self,
        api_key,
        *,
        transport=None,
        sleep=None,
        base_url="https://server.smartlead.ai",
        max_retries=5,
        timeout=30,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self.timeout = timeout
        self._transport = transport or _default_transport()
        if sleep is None:
            import time

            sleep = time.sleep
        self._sleep = sleep

    def list_campaigns(self):
        return self._request(CAMPAIGNS_PATH, {})

    def campaign_stats(self, campaign_id, start_date, end_date):
        """Return normalized stats for one campaign over [start_date, end_date], or None when
        the API has no data for it. Raises StatsResolutionError if data is present but the range
        cannot be confirmed."""
        data = self._request(
            f"{CAMPAIGNS_PATH}/{campaign_id}/statistics",
            {"start_date": start_date, "end_date": end_date},
        )
        if not data:
            return None
        self._assert_date_range(data, start_date, end_date)
        return self._normalize(data)

    def fetch_campaign_stats(self, campaign_ids, start_date, end_date):
        """Fetch stats for several campaigns, keyed by campaign id. A campaign the API returns
        no stats for emits a named warning to stderr and is omitted (never silently zeroed)."""
        out = {}
        for cid in campaign_ids:
            stats = self.campaign_stats(cid, start_date, end_date)
            if stats is None:
                print(
                    f"warning: SmartLead campaign {cid} returned no stats for "
                    f"{start_date}..{end_date}; omitting it from the digest",
                    file=sys.stderr,
                )
                continue
            out[cid] = stats
        return out

    def _request(self, path, params):
        url = self.base_url + path
        query = dict(params)
        query["api_key"] = self.api_key
        attempt = 0
        while True:
            resp = self._call(url, query)
            if resp.status_code == 429:
                if attempt >= self.max_retries:
                    raise SmartLeadAPIError("SmartLead rate limit: retries exhausted (429)")
                self._sleep(_retry_delay(resp, attempt))
                attempt += 1
                continue
            if resp.status_code >= 400:
                raise SmartLeadAPIError(f"SmartLead request failed: HTTP {resp.status_code}")
            return resp.json()

    def _call(self, url, query):
        try:
            return self._transport("GET", url, query, self.timeout)
        except SmartLeadAPIError:
            raise
        except Exception as exc:  # connection / timeout / transport-level failure
            raise SmartLeadAPIError(f"SmartLead request error: {exc}") from exc

    @staticmethod
    def _assert_date_range(data, start_date, end_date):
        if isinstance(data, dict):
            if any(data.get(k) for k in PER_DAY_KEYS):
                return
            echoed_start = data.get("start_date") or data.get("from_date")
            echoed_end = data.get("end_date") or data.get("to_date")
            if echoed_start == start_date and echoed_end == end_date:
                return
        raise StatsResolutionError(
            f"SmartLead stats could not be confirmed as scoped to {start_date}..{end_date} "
            "(no per-day breakdown and no matching start_date/end_date echo); refusing to "
            "present lifetime aggregates as weekly figures"
        )

    @staticmethod
    def _normalize(data):
        sent = _int(data, "sent_count", "sent", "sent_email_count")
        opens = _int(data, "open_count", "unique_open_count", "opens")
        replies = _int(data, "reply_count", "unique_reply_count", "replies")
        bounces = _int(data, "bounce_count", "bounced_count", "bounces")
        return {
            "opens": opens,
            "replies": replies,
            "bounces": bounces,
            "sent": sent,
            "open_rate": opens / sent if sent else 0.0,
            "reply_rate": replies / sent if sent else 0.0,
        }


class SmartLeadAPIError(RuntimeError):
    pass


class StatsResolutionError(RuntimeError):
    pass


def _int(data, *keys):
    for k in keys:
        v = data.get(k)
        if v is not None:
            try:
                return int(v)
            except (TypeError, ValueError):
                continue
    return 0


def _retry_delay(resp, attempt):
    retry_after = (resp.headers or {}).get("Retry-After")
    if retry_after:
        try:
            return float(retry_after)
        except (TypeError, ValueError):
            pass
    return float(2 ** attempt)


def _default_transport():
    def transport(method, url, params, timeout):
        import requests

        return requests.request(method, url, params=params, timeout=timeout)

    return transport
