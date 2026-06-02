"""ApolloClient - paged phone-call search with 429-aware backoff.

A thin wrapper over the Apollo REST API, kept shallow on purpose: every quirk of the raw
JSON is flattened in ``_normalize`` so the pure modules downstream see one stable shape.
Validated by the manual end-to-end run, not unit-tested for transport details beyond the
paging / backoff / window behavior the contract calls for.

The transport and sleep are injectable so the behavior can be exercised without a network
or real waits. In production the default transport is a small ``requests`` wrapper, built
lazily so importing this module never requires ``requests`` to be installed.
"""

CALLS_PATH = "/api/v1/phone_calls/search"


class ApolloClient:
    def __init__(
        self,
        api_key,
        *,
        transport=None,
        sleep=None,
        base_url="https://api.apollo.io",
        per_page=100,
        max_retries=5,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.per_page = per_page
        self.max_retries = max_retries
        self._transport = transport or _default_transport()
        if sleep is None:
            import time

            sleep = time.sleep
        self._sleep = sleep

    def search_calls(self, rep_cfg, since=None):
        user_id = rep_cfg.get("apollo_user_id")
        if not user_id:
            raise ApolloError("rep config missing apollo_user_id; refusing to query all users")
        out = []
        page = 1
        while True:
            payload = {
                "page": page,
                "per_page": self.per_page,
                "user_ids": [user_id],
            }
            if since:
                payload["call_created_at"] = {"min": since}
            data = self._post(CALLS_PATH, payload)
            records = data.get("phone_calls", []) or []
            for raw in records:
                call = self._normalize(raw)
                if since and (call.get("date") or "") < since:
                    continue
                out.append(call)
            pagination = data.get("pagination", {}) or {}
            total_pages = pagination.get("total_pages", page)
            if not records or page >= total_pages:
                break
            page += 1
        return out

    def _post(self, path, payload):
        url = self.base_url + path
        headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "X-Api-Key": self.api_key,
        }
        attempt = 0
        while True:
            resp = self._transport("POST", url, headers, payload)
            if resp.status_code == 429:
                if attempt >= self.max_retries:
                    raise ApolloError("Apollo rate limit: retries exhausted (429)")
                self._sleep(_retry_delay(resp, attempt))
                attempt += 1
                continue
            if resp.status_code >= 400:
                raise ApolloError(f"Apollo request failed: HTTP {resp.status_code}")
            return resp.json()

    @staticmethod
    def _normalize(raw):
        contact = raw.get("contact") or {}
        prospect = (
            raw.get("contact_name")
            or contact.get("name")
            or " ".join(
                p for p in [contact.get("first_name"), contact.get("last_name")] if p
            ).strip()
            or raw.get("to_name")
            or ""
        )
        timestamp = (
            raw.get("created_at")
            or raw.get("call_created_at")
            or raw.get("started_at")
            or ""
        )
        date = timestamp[:10] if timestamp else ""
        return {
            "id": str(raw.get("id") or raw.get("call_id") or ""),
            "timestamp": timestamp,
            "date": date,
            "prospect": prospect,
            "disposition": raw.get("disposition") or raw.get("label") or "",
            "phone": raw.get("phone_number") or raw.get("to_number") or "",
            "duration_sec": raw.get("duration") or raw.get("duration_seconds"),
            "recording_url": raw.get("recording_url") or raw.get("call_recording_url") or "",
        }


class ApolloError(RuntimeError):
    pass


def _retry_delay(resp, attempt):
    retry_after = (resp.headers or {}).get("Retry-After")
    if retry_after:
        try:
            return float(retry_after)
        except (TypeError, ValueError):
            pass
    return float(2 ** attempt)


def _default_transport():
    def transport(method, url, headers, json):
        import requests

        return requests.request(method, url, headers=headers, json=json, timeout=30)

    return transport
