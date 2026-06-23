from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from jobtrail.models import ProviderAccount, SyncWindowType, SyncWindowUnit
from jobtrail.utils.dates import date_to_utc_end_exclusive, date_to_utc_start, ensure_aware_utc


def parse_relative_window(choice: str) -> tuple[SyncWindowType, int | None, SyncWindowUnit | None]:
    value = choice.strip().lower()
    if value == "all available":
        return SyncWindowType.all, None, None
    parts = value.removeprefix("last ").split()
    if len(parts) != 2:
        raise ValueError("expected choices like 'last 90 days' or 'last 12 months'")
    return SyncWindowType.relative, int(parts[0]), SyncWindowUnit(parts[1])


def date_window(account: ProviderAccount, today: date | None = None) -> tuple[date | None, date | None]:
    today = today or date.today()
    if account.sync_window_type == SyncWindowType.all:
        return None, None
    if account.sync_window_type == SyncWindowType.absolute:
        return account.sync_start_date, account.sync_end_date or today
    value = account.relative_sync_value or 30
    unit = account.relative_sync_unit or SyncWindowUnit.days
    if unit == SyncWindowUnit.days:
        start = today - timedelta(days=value)
    elif unit == SyncWindowUnit.months:
        # ponytail: 30-day months are enough for email search windows; use dateutil if billing-grade dates matter.
        start = today - timedelta(days=value * 30)
    else:
        start = today - timedelta(days=value * 365)
    return start, today


def datetime_window(account: ProviderAccount, now: datetime | None = None) -> tuple[datetime | None, datetime | None]:
    now = ensure_aware_utc(now or datetime.now(UTC))
    if account.sync_window_type == SyncWindowType.all:
        return None, None
    if account.sync_window_type == SyncWindowType.absolute:
        start = date_to_utc_start(account.sync_start_date) if account.sync_start_date else None
        end = date_to_utc_end_exclusive(account.sync_end_date) if account.sync_end_date else None
        return start, end
    value = account.relative_sync_value or 30
    unit = account.relative_sync_unit or SyncWindowUnit.days
    if unit == SyncWindowUnit.days:
        start = now - timedelta(days=value)
    elif unit == SyncWindowUnit.months:
        # ponytail: 30-day months match existing email search windows; exact calendar math can wait.
        start = now - timedelta(days=value * 30)
    else:
        start = now - timedelta(days=value * 365)
    return start, now


def gmail_after_before(account: ProviderAccount) -> str:
    start, end = date_window(account)
    parts = []
    if start:
        parts.append(f"after:{start:%Y/%m/%d}")
    if end:
        parts.append(f"before:{end:%Y/%m/%d}")
    return " ".join(parts)
