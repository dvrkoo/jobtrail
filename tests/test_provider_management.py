from sqlmodel import Session, SQLModel, create_engine

from datetime import date

from jobtrail.models import ProviderAccount, SyncWindowType, SyncWindowUnit
from jobtrail.services.providers import set_enabled, set_labels_enabled, set_provider_window, set_relative_window


def test_provider_enable_disable_labels_and_window() -> None:
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as db:
        account = ProviderAccount(provider="gmail", account_email="a@example.com")
        db.add(account)
        db.commit()
        db.refresh(account)
        assert set_enabled(db, account.id, False)
        assert not db.get(ProviderAccount, account.id).enabled
        assert set_enabled(db, account.id, True)
        assert set_labels_enabled(db, account.id, True)
        assert db.get(ProviderAccount, account.id).labels_enabled
        assert set_relative_window(db, account.id, "last 24 months")
        refreshed = db.get(ProviderAccount, account.id)
        assert refreshed.relative_sync_value == 24
        assert refreshed.relative_sync_unit == SyncWindowUnit.months


def test_provider_set_window_persists_relative_days_without_credentials(monkeypatch) -> None:
    monkeypatch.setattr("jobtrail.providers.gmail_imap.store_password", lambda *_: (_ for _ in ()).throw(AssertionError("credential touched")))
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as db:
        account = ProviderAccount(provider="gmail_imap", account_email="a@example.com")
        db.add(account)
        db.commit()
        db.refresh(account)
        updated = set_provider_window(db, account.id, relative=30, unit="days")
        assert updated.sync_window_type == SyncWindowType.relative
        assert updated.relative_sync_value == 30
        assert updated.relative_sync_unit == SyncWindowUnit.days


def test_provider_set_window_persists_relative_months() -> None:
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as db:
        account = ProviderAccount(provider="gmail_imap", account_email="a@example.com")
        db.add(account)
        db.commit()
        db.refresh(account)
        updated = set_provider_window(db, account.id, relative=12, unit="months")
        assert updated.relative_sync_value == 12
        assert updated.relative_sync_unit == SyncWindowUnit.months


def test_provider_set_window_persists_absolute() -> None:
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as db:
        account = ProviderAccount(provider="gmail_imap", account_email="a@example.com")
        db.add(account)
        db.commit()
        db.refresh(account)
        updated = set_provider_window(db, account.id, start=date(2025, 1, 1), end=date(2026, 6, 23))
        assert updated.sync_window_type == SyncWindowType.absolute
        assert updated.sync_start_date == date(2025, 1, 1)
        assert updated.sync_end_date == date(2026, 6, 23)
