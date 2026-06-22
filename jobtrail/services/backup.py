from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from sqlmodel import Session, select

from jobtrail.config import load_config
from jobtrail.models import Application, EmailEvent, ProviderAccount


DATE_FIELDS = {"sync_start_date", "sync_end_date"}
DATETIME_FIELDS = {
    "application_date",
    "last_update_date",
    "last_email_date",
    "created_at",
    "updated_at",
    "received_at",
    "last_sync_at",
}


def encode(value: Any) -> Any:
    if isinstance(value, datetime | date):
        return value.isoformat()
    return value


def dump_model(model) -> dict[str, Any]:
    return {key: encode(value) for key, value in model.model_dump().items() if key != "auth_state_path"}


def decode_dates(item: dict[str, Any]) -> dict[str, Any]:
    for key, value in list(item.items()):
        if not value:
            continue
        if key in DATETIME_FIELDS and isinstance(value, str):
            item[key] = datetime.fromisoformat(value.replace("Z", "+00:00"))
        elif key in DATE_FIELDS and isinstance(value, str):
            item[key] = date.fromisoformat(value)
    return item


def export_backup(db: Session, path: Path) -> Path:
    data = {
        "version": 1,
        "created_at": datetime.now(UTC).isoformat(),
        "config": load_config().model_dump(exclude={"created_at", "updated_at"}),
        "applications": [dump_model(item) for item in db.exec(select(Application)).all()],
        "email_events": [dump_model(item) for item in db.exec(select(EmailEvent)).all()],
        "provider_accounts": [dump_model(item) for item in db.exec(select(ProviderAccount)).all()],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))
    return path


def import_backup(db: Session, path: Path) -> dict[str, int]:
    data = json.loads(path.read_text())
    counts = {"applications": 0, "email_events": 0, "provider_accounts": 0}
    for item in data.get("applications", []):
        item = decode_dates(item)
        if item.get("id") and db.get(Application, item["id"]):
            continue
        db.add(Application(**item))
        counts["applications"] += 1
    for item in data.get("email_events", []):
        item = decode_dates(item)
        if item.get("message_id") and db.exec(select(EmailEvent).where(EmailEvent.message_id == item["message_id"])).first():
            continue
        db.add(EmailEvent(**item))
        counts["email_events"] += 1
    for item in data.get("provider_accounts", []):
        item = decode_dates(item)
        exists = db.exec(
            select(ProviderAccount).where(
                ProviderAccount.provider == item.get("provider"),
                ProviderAccount.account_email == item.get("account_email"),
            )
        ).first()
        if exists:
            continue
        db.add(ProviderAccount(**item))
        counts["provider_accounts"] += 1
    db.commit()
    return counts
