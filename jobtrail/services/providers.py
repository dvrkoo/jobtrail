from __future__ import annotations

from datetime import date

from sqlmodel import Session, select

from jobtrail.models import ProviderAccount, SyncWindowType, SyncWindowUnit, now_utc
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


def window_label(account: ProviderAccount) -> str:
    if account.sync_window_type == SyncWindowType.all:
        return "all"
    if account.sync_window_type == SyncWindowType.absolute:
        return f"{account.sync_start_date or ''}..{account.sync_end_date or ''}"
    unit = account.relative_sync_unit.value if account.relative_sync_unit else SyncWindowUnit.days.value
    return f"last {account.relative_sync_value or 30} {unit}"


def set_provider_window(
    db: Session,
    provider_account_id: int,
    *,
    all_available: bool = False,
    relative: int | None = None,
    unit: str | SyncWindowUnit | None = None,
    start: date | None = None,
    end: date | None = None,
) -> ProviderAccount | None:
    account = db.get(ProviderAccount, provider_account_id)
    if not account:
        return None
    if all_available:
        account.sync_window_type = SyncWindowType.all
        account.sync_start_date = None
        account.sync_end_date = None
        account.relative_sync_value = None
        account.relative_sync_unit = None
    elif start:
        set_absolute_window(account, start, end)
    elif relative is not None:
        account.sync_window_type = SyncWindowType.relative
        account.sync_start_date = None
        account.sync_end_date = None
        account.relative_sync_value = relative
        account.relative_sync_unit = SyncWindowUnit(unit or SyncWindowUnit.days)
        account.updated_at = now_utc()
    else:
        raise ValueError("choose --all, --relative/--days/--months, or --start")
    db.add(account)
    db.commit()
    db.refresh(account)
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


def set_enabled(db: Session, provider_account_id: int, enabled: bool) -> bool:
    account = db.get(ProviderAccount, provider_account_id)
    if not account:
        return False
    account.enabled = enabled
    account.updated_at = now_utc()
    db.commit()
    return True


def set_labels_enabled(db: Session, provider_account_id: int, enabled: bool) -> bool:
    account = db.get(ProviderAccount, provider_account_id)
    if not account:
        return False
    account.labels_enabled = enabled
    account.updated_at = now_utc()
    db.commit()
    return True


def set_relative_window(db: Session, provider_account_id: int, choice: str) -> bool:
    account = db.get(ProviderAccount, provider_account_id)
    if not account:
        return False
    window_type, value, unit = parse_relative_window(choice)
    account.sync_window_type = window_type
    account.sync_start_date = None
    account.sync_end_date = None
    account.relative_sync_value = value
    account.relative_sync_unit = unit
    account.updated_at = now_utc()
    db.commit()
    return True
