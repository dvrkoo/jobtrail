from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlmodel import Session, select

from jobtrail.models import Application, Status


DEFAULT_THRESHOLDS = {
    Status.applied: 14,
    Status.pending: 14,
    Status.assessment: 7,
    Status.interview: 5,
    Status.ghosted: 0,
}
ACTIVE_STATUSES = {Status.applied, Status.pending, Status.assessment, Status.interview}


@dataclass
class FollowupCandidate:
    application: Application
    days_stale: int
    suggested_action: str


def days_since_update(app: Application, now: datetime | None = None) -> int:
    now = now or datetime.now(UTC)
    last = app.last_update_date or app.last_email_date or app.application_date or app.created_at
    if last.tzinfo is None:
        last = last.replace(tzinfo=UTC)
    return max((now - last).days, 0)


def suggested_action(status: Status) -> str:
    return {
        Status.applied: "Send polite follow-up",
        Status.pending: "Send polite follow-up",
        Status.assessment: "Check assessment deadline / follow up",
        Status.interview: "Ask about next steps",
        Status.ghosted: "Archive mentally or send final follow-up",
    }.get(status, "Review manually")


def followup_candidates(
    db: Session,
    *,
    include_all: bool = False,
    status: Status | None = None,
    days: int | None = None,
    include_archived: bool = False,
    now: datetime | None = None,
) -> list[FollowupCandidate]:
    apps = db.exec(select(Application)).all()
    rows = []
    for app in apps:
        if app.archived and not include_archived:
            continue
        if status and app.status != status:
            continue
        if not status and app.status not in ACTIVE_STATUSES | {Status.ghosted}:
            continue
        stale = days_since_update(app, now=now)
        threshold = days if days is not None else DEFAULT_THRESHOLDS.get(app.status, 14)
        if include_all or stale >= threshold:
            rows.append(FollowupCandidate(app, stale, suggested_action(app.status)))
    return sorted(rows, key=lambda item: item.days_stale, reverse=True)
