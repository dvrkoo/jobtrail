from sqlmodel import Session, SQLModel, create_engine

from jobtrail.models import Application, ProviderAccount, Status
from jobtrail.ui.state import export_action, filtered_applications, followup_rows, overview, provider_rows


def test_ui_state_adapters(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("JOBTRAIL_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("JOBTRAIL_DATA_DIR", str(tmp_path / "data"))
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as db:
        db.add(Application(company="Acme", role="Engineer", status=Status.pending))
        db.add(ProviderAccount(provider="gmail", account_email="a@example.com"))
        db.commit()
        assert overview(db)["total"] == 1
        assert filtered_applications(db, company="acme")[0]["company"] == "Acme"
        assert provider_rows(db)[0]["provider"] == "gmail"
        assert followup_rows(db, include_all=True)[0]["suggested_action"] == "Send polite follow-up"
        kind, text = export_action(db, "markdown")
        assert kind == "text"
        assert "Acme" in text
