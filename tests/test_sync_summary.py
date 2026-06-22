from sqlmodel import Session, SQLModel, create_engine

from jobtrail.schemas import ProviderMessage
from jobtrail.services.sync import sync_messages_summary


def test_sync_summary_counts_duplicates() -> None:
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    messages = [
        ProviderMessage(id="1", thread_id="t1", sender="Acme <jobs@acme.example>", subject="Application received for Engineer position", snippet="thank you for applying", received_at="2026-06-01T00:00:00+00:00"),
        ProviderMessage(id="1", thread_id="t1", sender="Acme <jobs@acme.example>", subject="Application received for Engineer position", snippet="thank you for applying", received_at="2026-06-01T00:00:00+00:00"),
    ]
    with Session(engine) as db:
        summary = sync_messages_summary(db, messages, provider="gmail", dry_run=False)
    assert summary.messages_scanned == 2
    assert summary.events_detected == 1
    assert summary.applications_created == 1
    assert summary.skipped_duplicates == 1
