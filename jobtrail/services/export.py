from __future__ import annotations

import csv
import io

from sqlmodel import Session, select

from jobtrail.models import Application


FIELDS = ["id", "company", "role", "status", "application_date", "last_email_date", "confidence", "notes"]


def export_csv(db: Session) -> str:
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=FIELDS)
    writer.writeheader()
    for app in db.exec(select(Application).order_by(Application.id)).all():
        writer.writerow({field: getattr(app, field) for field in FIELDS})
    return out.getvalue()


def export_markdown(db: Session) -> str:
    rows = ["| ID | Company | Role | Status |", "|---:|---|---|---|"]
    for app in db.exec(select(Application).order_by(Application.id)).all():
        rows.append(f"| {app.id} | {app.company} | {app.role} | {app.status.value} |")
    return "\n".join(rows) + "\n"
