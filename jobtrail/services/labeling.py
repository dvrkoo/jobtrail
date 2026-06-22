from __future__ import annotations

from sqlmodel import Session, select

from jobtrail.models import EmailEvent, Status


LABELS = {
    Status.applied: "JobTrail/Applied",
    Status.rejected: "JobTrail/Rejected",
    Status.interview: "JobTrail/Interview",
    Status.assessment: "JobTrail/Assessment",
    Status.offer: "JobTrail/Offer",
    Status.ghosted: "JobTrail/Ghosted",
}


def thread_labels(db: Session) -> dict[str, str]:
    labels = {}
    for event in db.exec(select(EmailEvent)).all():
        label = LABELS.get(event.status_inferred)
        if event.thread_id and label:
            labels[event.thread_id] = label
    return labels
