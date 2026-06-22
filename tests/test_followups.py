from datetime import UTC, datetime, timedelta

from sqlmodel import Session, SQLModel, create_engine

from jobtrail.models import Application, Status
from jobtrail.services.followups import days_since_update, followup_candidates, suggested_action


def test_followup_candidate_selection_and_actions() -> None:
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    now = datetime.now(UTC)
    with Session(engine) as db:
        db.add(Application(company="A", role="R", status=Status.pending, last_update_date=now - timedelta(days=15)))
        db.add(Application(company="B", role="R", status=Status.rejected, last_update_date=now - timedelta(days=30)))
        db.add(Application(company="C", role="R", status=Status.interview, last_update_date=now - timedelta(days=4)))
        db.commit()
        rows = followup_candidates(db, now=now)
    assert len(rows) == 1
    assert rows[0].days_stale == 15
    assert rows[0].suggested_action == "Send polite follow-up"
    assert suggested_action(Status.interview) == "Ask about next steps"


def test_days_since_update_never_negative() -> None:
    now = datetime.now(UTC)
    app = Application(company="A", role="R", last_update_date=now + timedelta(days=1))
    assert days_since_update(app, now=now) == 0
