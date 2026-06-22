from __future__ import annotations

from datetime import date, timedelta

from jobtrail.models import ProviderAccount, SyncWindowType, SyncWindowUnit


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


def gmail_after_before(account: ProviderAccount) -> str:
    start, end = date_window(account)
    parts = []
    if start:
        parts.append(f"after:{start:%Y/%m/%d}")
    if end:
        parts.append(f"before:{end:%Y/%m/%d}")
    return " ".join(parts)
