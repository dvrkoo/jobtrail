from sqlmodel import Session, SQLModel, create_engine

from jobtrail.models import ProviderAccount
from jobtrail.services.providers import set_enabled, set_labels_enabled, set_relative_window
from jobtrail.models import SyncWindowUnit


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
