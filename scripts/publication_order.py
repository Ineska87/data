"""Compare evidenced Warsaw publication times without assuming missing seconds."""

import re
from datetime import date, datetime
from zoneinfo import ZoneInfo


WARSAW = ZoneInfo("Europe/Warsaw")
CLOCK = re.compile(r"(\d{1,2}):(\d{2})(?::(\d{2}))?")


def clock_interval(value):
    match = CLOCK.fullmatch(str(value or "").strip())
    if not match:
        return None
    hour, minute, second = int(match[1]), int(match[2]), int(match[3] or 0)
    if hour >= 24 or minute >= 60 or second >= 60:
        return None
    first = hour * 3600 + minute * 60 + second
    return first, first if match[3] is not None else first + 59


def publication_clock(published_at):
    """Read the local clock and keep the precision recorded in a zoned stamp."""
    if not published_at:
        return ""
    stamp = datetime.fromisoformat(str(published_at))
    if stamp.tzinfo is None:
        raise ValueError(f"Publication timestamp without timezone: {published_at}")
    has_seconds = re.search(r"[T ]\d{2}:\d{2}:\d{2}", str(published_at)) is not None
    return stamp.astimezone(WARSAW).strftime("%H:%M:%S" if has_seconds else "%H:%M")


def strictly_before(first_day, first_clock, second_day, second_clock):
    """Return None when available evidence cannot order two same-day publications."""
    first, second = date.fromisoformat(str(first_day)[:10]), date.fromisoformat(str(second_day)[:10])
    if first != second:
        return first < second
    first_range, second_range = clock_interval(first_clock), clock_interval(second_clock)
    if first_range is None or second_range is None:
        return None
    if first_range[1] < second_range[0]:
        return True
    if first_range[0] >= second_range[1]:
        return False
    return None
