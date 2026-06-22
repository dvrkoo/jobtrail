from __future__ import annotations

from datetime import datetime

from sqlmodel import Session

from jobtrail.models import Application, Status, now_utc


EDITABLE_FIELDS = {
    "company",
    "role",
    "location",
    "source",
    "job_url",
    "status",
    "application_date",
    "last_update_date",
    "notes",
    "confidence",
}


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def update_application(db: Session, application_id: int, **changes: object) -> Application | None:
    app = db.get(Application, application_id)
    if not app:
        return None
    changed_verified_field = False
    for key, value in changes.items():
        if value is None or key not in EDITABLE_FIELDS:
            continue
        if key == "status":
            value = Status(value)
        elif key in {"application_date", "last_update_date"} and isinstance(value, str):
            value = parse_datetime(value)
        elif key == "confidence":
            value = float(value)
        setattr(app, key, value)
        if key in {"company", "role", "status"}:
            changed_verified_field = True
    if changed_verified_field:
        app.manually_verified = True
    app.updated_at = now_utc()
    db.add(app)
    db.commit()
    db.refresh(app)
    return app


def set_archived(db: Session, application_id: int, archived: bool) -> bool:
    app = db.get(Application, application_id)
    if not app:
        return False
    app.archived = archived
    app.updated_at = now_utc()
    db.commit()
    return True
