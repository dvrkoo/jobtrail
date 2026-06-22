from __future__ import annotations

from sqlmodel import Session, select

from jobtrail.models import Application, Status
from jobtrail.services.followups import followup_candidates


def stats(db: Session) -> dict[str, float | int]:
    apps = db.exec(select(Application)).all()
    total = len(apps)
    archived = sum(app.archived for app in apps)
    counts = {status.value: sum(app.status == status for app in apps) for status in Status}
    return {
        "total": total,
        "active": total - archived,
        "archived": archived,
        "followups_due": len(followup_candidates(db)),
        "manually_verified": sum(app.manually_verified for app in apps),
        "rejected": counts["rejected"],
        "interviews": counts["interview"],
        "assessments": counts["assessment"],
        "offers": counts["offer"],
        "pending": counts["pending"],
        "ghosted": counts["ghosted"],
        "rejection_rate": round(counts["rejected"] / total, 2) if total else 0,
        "interview_rate": round(counts["interview"] / total, 2) if total else 0,
    }
