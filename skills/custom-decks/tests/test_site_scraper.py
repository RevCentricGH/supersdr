"""SiteScraper: fetch + tag-strip across a subpage list within per-subpage and total budgets.

Covers validation-contract assertions 6-9 and the required tests 35-37.
"""
from customdecks.site_scraper import SiteScraper


class FakeFetcher:
    """Returns canned raw HTML per URL and records the order URLs were fetched in."""

    def __init__(self, pages):
        self.pages = pages
        self.fetched = []

    def __call__(self, url):
        self.fetched.append(url)
        return self.pages[url]


def test_strips_html_tags_before_accounting():
    fetcher = FakeFetcher({"u1": "<p>Hello</p><div>World</div>"})
    result = SiteScraper(fetcher, per_subpage_budget=100, total_budget=100).scrape(["u1"])
    assert "<" not in result.text and ">" not in result.text
    assert "Hello" in result.text and "World" in result.text


def test_strips_script_and_style_contents():
    fetcher = FakeFetcher({"u1": "<style>p{color:red}</style><script>var a=1;</script><p>Keep</p>"})
    result = SiteScraper(fetcher, per_subpage_budget=200, total_budget=200).scrape(["u1"])
    assert "color:red" not in result.text
    assert "var a" not in result.text
    assert "Keep" in result.text


def test_truncates_each_page_to_per_subpage_budget():
    fetcher = FakeFetcher({"u1": "b" * 50})
    result = SiteScraper(fetcher, per_subpage_budget=10, total_budget=1000).scrape(["u1"])
    assert len(result.text) == 10


def test_stops_fetching_once_total_budget_reached():
    fetcher = FakeFetcher({"u1": "a" * 50, "u2": "a" * 50, "u3": "a" * 50})
    result = SiteScraper(fetcher, per_subpage_budget=100, total_budget=100).scrape(["u1", "u2", "u3"])
    assert fetcher.fetched == ["u1", "u2"]
    assert "u3" not in fetcher.fetched
    assert result.fetched == ["u1", "u2"]
    assert len(result.text) == 100


def test_does_not_overshoot_total_budget():
    fetcher = FakeFetcher({"u1": "a" * 50, "u2": "a" * 50, "u3": "a" * 50})
    result = SiteScraper(fetcher, per_subpage_budget=100, total_budget=70).scrape(["u1", "u2", "u3"])
    assert len(result.text) == 70
    assert fetcher.fetched == ["u1", "u2"]
