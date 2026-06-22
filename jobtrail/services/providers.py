from __future__ import annotations

from datetime import date

from sqlmodel import Session, select

from jobtrail.models import ProviderAccount, SyncWindowType, now_utc
from jobtrail.utils.windows import parse_relative_window


def add_provider_account(
    db: Session,
    provider: str,
    account_email: str,
    labels_enabled: bool = False,
    sync_choice: str = "last 12 months",
    sync_start_date: date | None = None,
    sync_end_date: date | None = None,
) -> ProviderAccount:
    window_type, value, unit = parse_relative_window(sync_choice)
    account = ProviderAccount(
        provider=provider,
        account_email=account_email,
        labels_enabled=labels_enabled,
        sync_window_type=window_type,
        sync_start_date=sync_start_date,
        sync_end_date=sync_end_date,
        relative_sync_value=value,
        relative_sync_unit=unit,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def set_absolute_window(
    account: ProviderAccount, start: date, end: date | None = None
) -> ProviderAccount:
    account.sync_window_type = SyncWindowType.absolute
    account.sync_start_date = start
    account.sync_end_date = end
    account.relative_sync_value = None
    account.relative_sync_unit = None
    account.updated_at = now_utc()
    return account


def enabled_accounts(db: Session, provider: str | None = None, account: str | None = None):
    query = select(ProviderAccount).where(ProviderAccount.enabled == True)  # noqa: E712
    if provider:
        query = query.where(ProviderAccount.provider == provider)
    if account:
        query = query.where(ProviderAccount.account_email == account)
    return db.exec(query).all()


def disable_or_delete(db: Session, provider_account_id: int, delete: bool = False) -> bool:
    account = db.get(ProviderAccount, provider_account_id)
    if not account:
        return False
    if delete:
        db.delete(account)
    else:
        account.enabled = False
        account.updated_at = now_utc()
    db.commit()
    return True
