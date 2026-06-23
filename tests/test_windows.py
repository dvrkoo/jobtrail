from datetime import UTC, date, datetime

from jobtrail.models import ProviderAccount, SyncWindowType, SyncWindowUnit
from jobtrail.utils.windows import date_window, datetime_window, gmail_after_before, parse_relative_window


def test_parse_relative_window() -> None:
    assert parse_relative_window("last 90 days") == (SyncWindowType.relative, 90, SyncWindowUnit.days)
    assert parse_relative_window("all available") == (SyncWindowType.all, None, None)


def test_relative_date_window() -> None:
    account = ProviderAccount(provider="gmail", account_email="a@example.com", relative_sync_value=30, relative_sync_unit=SyncWindowUnit.days)
    assert date_window(account, today=date(2026, 6, 22)) == (date(2026, 5, 23), date(2026, 6, 22))


def test_absolute_and_gmail_window() -> None:
    account = ProviderAccount(
        provider="gmail",
        account_email="a@example.com",
        sync_window_type=SyncWindowType.absolute,
        sync_start_date=date(2026, 1, 1),
        sync_end_date=date(2026, 2, 1),
    )
    assert date_window(account) == (date(2026, 1, 1), date(2026, 2, 1))
    assert gmail_after_before(account) == "after:2026/01/01 before:2026/02/01"


def test_datetime_window_returns_aware_utc() -> None:
    account = ProviderAccount(provider="gmail", account_email="a@example.com", relative_sync_value=30, relative_sync_unit=SyncWindowUnit.days)
    start, end = datetime_window(account, now=datetime(2026, 6, 23, 12, 0))
    assert start.tzinfo == UTC
    assert end == datetime(2026, 6, 23, 12, 0, tzinfo=UTC)


def test_absolute_datetime_window_end_exclusive() -> None:
    account = ProviderAccount(
        provider="gmail",
        account_email="a@example.com",
        sync_window_type=SyncWindowType.absolute,
        sync_start_date=date(2026, 1, 1),
        sync_end_date=date(2026, 1, 31),
    )
    assert datetime_window(account) == (datetime(2026, 1, 1, tzinfo=UTC), datetime(2026, 2, 1, tzinfo=UTC))
