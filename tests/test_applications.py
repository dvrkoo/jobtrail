from sqlmodel import Session, SQLModel, create_engine

from jobtrail.models import Application, Status
from jobtrail.services.applications import set_archived, update_application


def test_update_application_sets_manual_verified() -> None:
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as db:
        app = Application(company="Bad", role="Bad", status=Status.pending)
        db.add(app)
        db.commit()
        db.refresh(app)
        updated = update_application(db, app.id, company="Daon", role="Data Scientist", status="interview")
        assert updated.company == "Daon"
        assert updated.status == Status.interview
        assert updated.manually_verified


def test_archive_unarchive() -> None:
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as db:
        app = Application(company="A", role="R")
        db.add(app)
        db.commit()
        db.refresh(app)
        assert set_archived(db, app.id, True)
        assert db.get(Application, app.id).archived
        assert set_archived(db, app.id, False)
        assert not db.get(Application, app.id).archived
