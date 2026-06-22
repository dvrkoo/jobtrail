from datetime import date

from jobtrail.models import ProviderAccount, SyncWindowType, SyncWindowUnit
from jobtrail.utils.windows import date_window, gmail_after_before, parse_relative_window


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
