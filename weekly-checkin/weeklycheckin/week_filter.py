"""ISO-8601 week bounds.

``week_bounds("2026-W22")`` returns the Monday..Sunday date pair for that ISO week as two
``datetime.date`` objects. The week is Monday-anchored (ISO 8601 weekday 1..7). A bad format,
or a week that does not exist for the year (week 53 of a 52-week year), raises ``ValueError``
with the offending value.
"""
import datetime
import re

_WEEK_RE = re.compile(r"^(\d{4})-W(\d{2})$")


def week_bounds(week):
    m = _WEEK_RE.match((week or "").strip())
    if not m:
        raise ValueError(
            f"invalid week '{week}'; expected YYYY-WNN (ISO 8601 week, Monday-anchored), e.g. 2026-W22"
        )
    year, num = int(m.group(1)), int(m.group(2))
    try:
        start = datetime.date.fromisocalendar(year, num, 1)
        end = datetime.date.fromisocalendar(year, num, 7)
    except ValueError as exc:
        raise ValueError(f"invalid ISO week '{week}': {exc}") from exc
    return start, end
