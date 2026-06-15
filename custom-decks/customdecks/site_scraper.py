"""SiteScraper - fetch the prospect site across a fixed subpage list, strip HTML, and keep
the text within per-subpage and total character budgets.

Each page is fetched, stripped of all markup, truncated to ``per_subpage_budget``, then
appended to the running total - but only the portion that fits under ``total_budget`` is
kept, and once the total is reached no further URLs are fetched. The total therefore never
overshoots the budget. The ``fetcher`` is injected as a callable ``(url) -> raw_html`` so
the budget logic can be tested without the network; ``requests_fetcher`` builds the real one.
"""
import html
import re

_SCRIPT_STYLE = re.compile(r"<(script|style)\b[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


class ScrapeResult:
    def __init__(self, text, fetched):
        self.text = text
        self.fetched = fetched


def strip_html(raw):
    without_blocks = _SCRIPT_STYLE.sub(" ", raw)
    no_tags = _TAG.sub(" ", without_blocks)
    unescaped = html.unescape(no_tags)
    return _WS.sub(" ", unescaped).strip()


class SiteScraper:
    def __init__(self, fetcher, per_subpage_budget, total_budget):
        self._fetcher = fetcher
        self.per_subpage_budget = per_subpage_budget
        self.total_budget = total_budget

    def scrape(self, urls):
        parts = []
        fetched = []
        used = 0
        for url in urls:
            if used >= self.total_budget:
                break
            try:
                raw = self._fetcher(url)
            except Exception:
                continue
            stripped = strip_html(raw)[: self.per_subpage_budget]
            remaining = self.total_budget - used
            piece = stripped[:remaining]
            if not piece:
                continue
            parts.append(piece)
            fetched.append(url)
            used += len(piece)
        return ScrapeResult(text="".join(parts), fetched=fetched)


def requests_fetcher(*, transport=None, user_agent="custom-decks/1.0"):
    """Real HTTP fetcher callable. Returns the response body text, or empty on any error so a
    single dead subpage never sinks the whole scrape."""

    def fetch(url):
        import requests

        get = transport or requests.get
        resp = get(url, headers={"User-Agent": user_agent}, timeout=30)
        if getattr(resp, "status_code", 200) >= 400:
            return ""
        return resp.text or ""

    return fetch
