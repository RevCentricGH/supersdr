"""Backfill window start date (supports contract 5)."""
import datetime

from mastertracker.config import compute_backfill_start


def test_backfill_start_is_today_minus_window():
    today = datetime.date(2026, 5, 31)
    assert compute_backfill_start({"backfill_days": 30}, today=today) == "2026-05-01"


def test_no_backfill_days_means_no_lower_bound():
    assert compute_backfill_start({}, today=datetime.date(2026, 5, 31)) is None
