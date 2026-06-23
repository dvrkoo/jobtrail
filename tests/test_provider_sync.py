from typer.testing import CliRunner
from sqlmodel import Session, SQLModel, create_engine

from jobtrail.cli import app
from jobtrail.db import init_db, session
from jobtrail.models import ProviderAccount, SyncWindowUnit
from jobtrail.providers.gmail import GmailProvider
from jobtrail.providers.gmail_imap import GmailImapProvider
from jobtrail.schemas import ProviderMessage
from jobtrail.services.sync import sync_provider_account


runner = CliRunner()


def test_sync_uses_provider_specific_window(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("JOBTRAIL_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("JOBTRAIL_DATA_DIR", str(tmp_path / "data"))
    seen = []

    def fake_search(self, window_query=None, max_messages=None):
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
        summary = sync_provider_account(db, account)
        assert summary.events_detected == 1
        assert summary.applications_created == 1
    assert seen and "after:" in seen[0]


def test_outlook_stub_returns_error() -> None:
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as db:
        account = ProviderAccount(provider="outlook", account_email="a@example.com")
        db.add(account)
        db.commit()
        db.refresh(account)
        summary = sync_provider_account(db, account)
        assert summary.status == "error"
        assert "Outlook" in summary.error


def test_gmail_imap_sync_dispatch(monkeypatch) -> None:
    def fake_search(self, window_query=None, max_messages=None):
        return [
            ProviderMessage(
                id="imap-1",
                thread_id="imap-1",
                sender="Acme <jobs@acme.example>",
                subject="Application received for Engineer position",
                snippet="thank you for applying",
                received_at="2026-06-01T00:00:00+00:00",
                account_email=self.account_email,
            )
        ]

    monkeypatch.setattr(GmailImapProvider, "search_messages", fake_search)
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as db:
        account = ProviderAccount(provider="gmail_imap", account_email="a@example.com")
        db.add(account)
        db.commit()
        db.refresh(account)
        summary = sync_provider_account(db, account)
        assert summary.events_detected == 1
        assert summary.provider == "gmail_imap"


def test_sync_resolves_persisted_provider_window(monkeypatch) -> None:
    seen = []

    def fake_search(self, window_query=None, max_messages=None):
        seen.append(window_query)
        return []

    monkeypatch.setattr(GmailImapProvider, "search_messages", fake_search)
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as db:
        account = ProviderAccount(provider="gmail_imap", account_email="a@example.com", relative_sync_value=30, relative_sync_unit=SyncWindowUnit.days)
        db.add(account)
        db.commit()
        db.refresh(account)
        sync_provider_account(db, account)
    assert seen and "after:" in seen[0]


def test_sync_runtime_days_override_not_saved(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("JOBTRAIL_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("JOBTRAIL_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setattr(GmailImapProvider, "search_messages", lambda self, window_query=None, max_messages=None: [])
    init_db()
    with session() as db:
        db.add(ProviderAccount(provider="gmail_imap", account_email="a@example.com", relative_sync_value=12, relative_sync_unit=SyncWindowUnit.months))
        db.commit()
    result = runner.invoke(app, ["sync", "--provider", "gmail_imap", "--days", "30", "--dry-run"])
    assert result.exit_code == 0
    with session() as db:
        account = db.get(ProviderAccount, 1)
        assert account.relative_sync_value == 12
        assert account.relative_sync_unit == SyncWindowUnit.months


def test_sync_runtime_days_override_saved(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("JOBTRAIL_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("JOBTRAIL_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setattr(GmailImapProvider, "search_messages", lambda self, window_query=None, max_messages=None: [])
    init_db()
    with session() as db:
        db.add(ProviderAccount(provider="gmail_imap", account_email="a@example.com", relative_sync_value=12, relative_sync_unit=SyncWindowUnit.months))
        db.commit()
    result = runner.invoke(app, ["sync", "--provider", "gmail_imap", "--days", "30", "--save-window", "--dry-run"])
    assert result.exit_code == 0
    with session() as db:
        account = db.get(ProviderAccount, 1)
        assert account.relative_sync_value == 30
        assert account.relative_sync_unit == SyncWindowUnit.days


def test_sync_command_returns_after_summary_and_verbose(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("JOBTRAIL_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("JOBTRAIL_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setattr(GmailImapProvider, "search_messages", lambda self, window_query=None, max_messages=None: [])
    init_db()
    with session() as db:
        db.add(ProviderAccount(provider="gmail_imap", account_email="a@example.com"))
        db.commit()
    result = runner.invoke(app, ["sync", "--provider", "gmail_imap", "--dry-run", "--verbose"])
    assert result.exit_code == 0
    assert "resolved_date_range" in result.output
    assert "Sync finished; exiting." in result.output
