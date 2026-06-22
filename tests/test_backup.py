import json

from sqlmodel import Session, SQLModel, create_engine, select

from jobtrail.models import Application, ProviderAccount
from jobtrail.services.backup import export_backup, import_backup


def test_backup_excludes_auth_state_and_imports(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("JOBTRAIL_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("JOBTRAIL_DATA_DIR", str(tmp_path / "data"))
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    backup = tmp_path / "backup.json"
    with Session(engine) as db:
        db.add(Application(company="A", role="R"))
        db.add(ProviderAccount(provider="gmail", account_email="a@example.com", auth_state_path="secret-token-path"))
        db.commit()
        export_backup(db, backup)
    data = json.loads(backup.read_text())
    assert "auth_state_path" not in data["provider_accounts"][0]
    assert "secret-token-path" not in backup.read_text()

    engine2 = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine2)
    with Session(engine2) as db:
        counts = import_backup(db, backup)
        assert counts["applications"] == 1
        assert db.exec(select(Application)).one().company == "A"
