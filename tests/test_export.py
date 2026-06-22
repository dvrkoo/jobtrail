from sqlmodel import Session, SQLModel, create_engine

from jobtrail.models import Application, Status
from jobtrail.services.export import export_csv, export_markdown


def test_exports() -> None:
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as db:
        db.add(Application(company="Acme", role="Engineer", status=Status.applied, confidence=0.8))
        db.commit()
        assert "company,role" in export_csv(db)
        assert "| Acme | Engineer | applied |" in export_markdown(db)
