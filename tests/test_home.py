from datetime import UTC, datetime

from sqlmodel import Session, SQLModel, create_engine

from jobtrail.models import Application, ProviderAccount, Status
from jobtrail.services.home import home_data, suggested_actions


def test_home_data_and_suggestions() -> None:
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as db:
        db.add(ProviderAccount(provider="gmail", account_email="a@example.com", last_sync_at=datetime.now(UTC), last_sync_status="ok"))
        db.add(Application(company="Acme", role="Engineer", status=Status.pending))
        db.commit()
        data = home_data(db)
    assert data["providers_count"] == 1
    assert data["enabled_providers_count"] == 1
    assert data["pending"] == 1
    assert "jobtrail list --status pending" in suggested_actions(data)


def test_suggest_provider_add_when_no_providers() -> None:
    data = {
        "providers_count": 0,
        "enabled_providers_count": 0,
        "last_sync_summary": "never",
        "total": 0,
        "pending": 0,
        "interviews": 0,
        "assessments": 0,
        "rejected": 0,
        "offers": 0,
        "ghosted": 0,
    }
    actions = suggested_actions(data)
    assert "jobtrail providers add" in actions
    assert "jobtrail sync --from-sample-json examples/sample_gmail_messages.json" in actions
