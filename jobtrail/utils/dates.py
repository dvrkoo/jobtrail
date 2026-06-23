from __future__ import annotations

from datetime import UTC, date, datetime, timedelta


def ensure_aware_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def date_to_utc_start(d: date) -> datetime:
    return datetime(d.year, d.month, d.day, tzinfo=UTC)


def date_to_utc_end_exclusive(d: date) -> datetime:
    return date_to_utc_start(d + timedelta(days=1))
