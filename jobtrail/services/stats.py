from __future__ import annotations

from sqlmodel import Session, select

from jobtrail.models import Application, Status


def stats(db: Session) -> dict[str, float | int]:
    apps = db.exec(select(Application)).all()
    total = len(apps)
    counts = {status.value: sum(app.status == status for app in apps) for status in Status}
    return {
        "total": total,
        "rejected": counts["rejected"],
        "interviews": counts["interview"],
        "assessments": counts["assessment"],
        "offers": counts["offer"],
        "pending": counts["pending"],
        "ghosted": counts["ghosted"],
        "rejection_rate": round(counts["rejected"] / total, 2) if total else 0,
        "interview_rate": round(counts["interview"] / total, 2) if total else 0,
    }
