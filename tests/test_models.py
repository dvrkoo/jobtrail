from datetime import UTC, datetime, timedelta

from sqlmodel import Session, SQLModel, create_engine, select

from jobtrail.models import Application, Status
from jobtrail.schemas import ProviderMessage
from jobtrail.services.sync import apply_ghosting, sync_messages


def mem_session() -> Session:
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_ghosting_heuristic() -> None:
    with mem_session() as db:
        db.add(Application(company="A", role="B", status=Status.applied, last_email_date=datetime.now(UTC) - timedelta(days=31)))
        db.commit()
        assert apply_ghosting(db, days=30) == 1
        assert db.exec(select(Application)).one().status == Status.ghosted


def test_deduplicates_by_thread() -> None:
    messages = [
        ProviderMessage(id="1", thread_id="t1", sender="Acme <jobs@acme.example>", subject="Application received", snippet="thank you for applying", received_at="2026-01-01T00:00:00+00:00"),
        ProviderMessage(id="2", thread_id="t1", sender="Acme <jobs@acme.example>", subject="Interview", snippet="schedule a call", received_at="2026-01-02T00:00:00+00:00"),
    ]
    with mem_session() as db:
        sync_messages(db, messages, provider="gmail", dry_run=False)
        assert len(db.exec(select(Application)).all()) == 1
        assert db.exec(select(Application)).one().status == Status.interview
