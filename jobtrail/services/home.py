from __future__ import annotations

from sqlmodel import Session, select

from jobtrail.models import ProviderAccount
from jobtrail.services.stats import stats


def home_data(db: Session) -> dict[str, int | str | None]:
    accounts = db.exec(select(ProviderAccount)).all()
    enabled = [account for account in accounts if account.enabled]
    last = max((account.last_sync_at for account in accounts if account.last_sync_at), default=None)
    data = stats(db)
    return {
        "providers_count": len(accounts),
        "enabled_providers_count": len(enabled),
        "last_sync_summary": str(last) if last else "never",
        "total": data["total"],
        "pending": data["pending"],
        "interviews": data["interviews"],
        "assessments": data["assessments"],
        "rejected": data["rejected"],
        "offers": data["offers"],
        "ghosted": data["ghosted"],
    }


def suggested_actions(data: dict[str, int | str | None]) -> list[str]:
    actions = []
    if data["providers_count"] == 0:
        actions.append("jobtrail providers add")
    elif data["last_sync_summary"] == "never":
        actions.append("jobtrail sync")
    if data["pending"]:
        actions.append("jobtrail list --status pending")
    if data["ghosted"]:
        actions.append("jobtrail list --status ghosted")
    if data["total"] == 0:
        actions.append("jobtrail sync --from-sample-json examples/sample_gmail_messages.json")
    return actions or ["jobtrail stats"]
