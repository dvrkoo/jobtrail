from sqlmodel import Session, SQLModel, create_engine

from jobtrail.models import ProviderAccount, SyncWindowUnit
from jobtrail.providers.gmail import GmailProvider
from jobtrail.schemas import ProviderMessage
from jobtrail.services.sync import sync_provider_account


def test_sync_uses_provider_specific_window(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("JOBTRAIL_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("JOBTRAIL_DATA_DIR", str(tmp_path / "data"))
    seen = []

    def fake_search(self, window_query=None):
        seen.append(window_query)
        return [
            ProviderMessage(
                id="1",
                thread_id="t1",
                sender="Acme <jobs@acme.example>",
                subject="Application received for Engineer position",
                snippet="thank you for applying",
                received_at="2026-06-01T00:00:00+00:00",
            )
        ]

    monkeypatch.setattr(GmailProvider, "search_messages", fake_search)
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as db:
        account = ProviderAccount(
            provider="gmail",
            account_email="a@example.com",
            relative_sync_value=90,
            relative_sync_unit=SyncWindowUnit.days,
        )
        db.add(account)
        db.commit()
        db.refresh(account)
        assert len(sync_provider_account(db, account)) == 1
    assert seen and "after:" in seen[0]
