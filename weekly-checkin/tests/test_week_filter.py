"""week_bounds: Monday-anchored ISO week bounds, with week 1 / week 53 edge cases."""
import datetime

import pytest

from weeklycheckin.week_filter import week_bounds


def test_week_22_is_monday_to_sunday():
    start, end = week_bounds("2026-W22")
    assert start == datetime.date(2026, 5, 25)
    assert end == datetime.date(2026, 5, 31)
    assert start.weekday() == 0  # Monday
    assert end.weekday() == 6  # Sunday


def test_week_one_spans_the_year_boundary():
    start, end = week_bounds("2026-W01")
    assert start == datetime.date(2025, 12, 29)
    assert end == datetime.date(2026, 1, 4)


def test_week_53_of_a_long_year():
    start, end = week_bounds("2020-W53")
    assert start == datetime.date(2020, 12, 28)
    assert end == datetime.date(2021, 1, 3)


def test_week_53_of_a_short_year_raises():
    with pytest.raises(ValueError):
        week_bounds("2021-W53")


def test_bad_format_raises_with_the_value():
    with pytest.raises(ValueError) as exc:
        week_bounds("2026-22")
    assert "2026-22" in str(exc.value)
