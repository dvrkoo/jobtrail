from __future__ import annotations

from pathlib import Path

from sqlmodel import Session, select

from jobtrail.config import load_config, settings, update_config
from jobtrail.models import Application, ProviderAccount, Status
from jobtrail.services.applications import set_archived, update_application
from jobtrail.services.export import export_csv, export_dir, export_latex, export_markdown, export_xlsx, timestamped_name
from jobtrail.services.followups import days_since_update, followup_candidates
from jobtrail.services.home import home_data
from jobtrail.services.providers import add_provider_account, set_enabled, set_labels_enabled, set_relative_window
from jobtrail.utils.windows import date_window


def overview(db: Session) -> dict[str, object]:
    data = home_data(db)
    apps = db.exec(select(Application).order_by(Application.updated_at.desc())).all()
    data["recent_applications"] = applications_rows(apps[:5])
    return data


def applications_rows(apps: list[Application]) -> list[dict[str, object]]:
    return [
        {
            "id": app.id,
            "company": app.company,
            "role": app.role,
            "status": app.status.value,
            "application_date": app.application_date,
            "last_update": app.last_update_date or app.last_email_date,
            "days_stale": days_since_update(app),
            "confidence": app.confidence,
            "manually_verified": app.manually_verified,
            "archived": app.archived,
        }
        for app in apps
    ]


def filtered_applications(
    db: Session,
    *,
    status: Status | None = None,
    archived: bool | None = None,
    manually_verified: bool | None = None,
    company: str = "",
    role: str = "",
) -> list[dict[str, object]]:
    apps = db.exec(select(Application).order_by(Application.last_update_date.desc())).all()
    if status:
        apps = [app for app in apps if app.status == status]
    if archived is not None:
        apps = [app for app in apps if app.archived == archived]
    if manually_verified is not None:
        apps = [app for app in apps if app.manually_verified == manually_verified]
    if company:
        apps = [app for app in apps if company.lower() in app.company.lower()]
    if role:
        apps = [app for app in apps if role.lower() in app.role.lower()]
    return applications_rows(apps)


def provider_rows(db: Session) -> list[dict[str, object]]:
    rows = []
    for account in db.exec(select(ProviderAccount).order_by(ProviderAccount.id)).all():
        start, end = date_window(account)
        rows.append(
            {
                "id": account.id,
                "provider": account.provider,
                "account_email": account.account_email,
                "enabled": account.enabled,
                "labels_enabled": account.labels_enabled,
                "sync_window": "all" if not start and not end else f"{start or ''}..{end or ''}",
                "last_sync": account.last_sync_at,
                "last_status": account.last_sync_status or "never",
            }
        )
    return rows


def followup_rows(db: Session, *, include_all: bool = False, status: Status | None = None, days: int | None = None, include_archived: bool = False) -> list[dict[str, object]]:
    return [
        {
            "id": item.application.id,
            "company": item.application.company,
            "role": item.application.role,
            "status": item.application.status.value,
            "days_stale": item.days_stale,
            "suggested_action": item.suggested_action,
            "confidence": item.application.confidence,
        }
        for item in followup_candidates(
            db,
            include_all=include_all,
            status=status,
            days=days,
            include_archived=include_archived,
        )
    ]


def export_action(db: Session, fmt: str, status: Status | None = None) -> tuple[str, str | Path]:
    cfg = settings()
    if fmt == "csv":
        return "text", export_csv(db)
    if fmt == "markdown":
        return "text", export_markdown(db, status=status)
    if fmt == "latex":
        return "text", export_latex(db, status=status)
    out = export_dir(cfg.data_dir)
    if fmt == "xlsx":
        path = out / timestamped_name("xlsx")
        return "file", export_xlsx(db, path)
    if fmt == "all":
        (out / timestamped_name("csv")).write_text(export_csv(db))
        (out / timestamped_name("md")).write_text(export_markdown(db))
        (out / timestamped_name("tex")).write_text(export_latex(db))
        export_xlsx(db, out / timestamped_name("xlsx"))
        return "dir", out
    raise ValueError("unknown export format")


def save_settings(**changes: object):
    return update_config(**changes)


def config_summary() -> dict[str, object]:
    cfg = settings()
    app_cfg = load_config()
    return {
        **app_cfg.model_dump(),
        "config_path": cfg.config_dir / "config.toml",
        "data_path": cfg.db_path,
        "token_path": cfg.token_dir,
    }


__all__ = [
    "add_provider_account",
    "set_enabled",
    "set_labels_enabled",
    "set_relative_window",
    "set_archived",
    "update_application",
]
