from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from sqlmodel import Session, select

from jobtrail.classifiers.rules import classify_email
from jobtrail.config import load_config
from jobtrail.models import Application, EmailEvent, ProviderAccount, Status, now_utc
from jobtrail.providers.gmail import GmailProvider
from jobtrail.schemas import ProviderMessage
from jobtrail.utils.windows import gmail_after_before
from jobtrail.utils.text import company_from_sender, normalize_key, role_from_text


TERMINAL_RANK = {
    Status.unknown: 0,
    Status.pending: 1,
    Status.applied: 2,
    Status.assessment: 3,
    Status.interview: 4,
    Status.rejected: 5,
    Status.offer: 6,
    Status.ghosted: 7,
}


@dataclass
class SyncSummary:
    provider: str
    account_email: str | None = None
    search_window: str = "sample"
    messages_scanned: int = 0
    events_detected: int = 0
    applications_created: int = 0
    applications_updated: int = 0
    skipped_duplicates: int = 0
    status: str = "ok"
    error: str | None = None
    lines: list[str] = field(default_factory=list)


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def find_application(db: Session, company: str, role: str, thread_id: str | None) -> Application | None:
    if thread_id:
        event = db.exec(select(EmailEvent).where(EmailEvent.thread_id == thread_id)).first()
        if event and event.application_id:
            return db.get(Application, event.application_id)
    company_key = normalize_key(company)
    role_key = normalize_key(role)
    for app in db.exec(select(Application)).all():
        if normalize_key(app.company) == company_key and normalize_key(app.role) == role_key:
            return app
    return None


def apply_ghosting(db: Session, days: int | None = None) -> int:
    cutoff = now_utc() - timedelta(days=days or load_config().ghosting_threshold_days)
    changed = 0
    apps = db.exec(select(Application).where(Application.status.in_([Status.applied, Status.pending]))).all()
    for app in apps:
        last = app.last_email_date
        if last and last.tzinfo is None:
            last = last.replace(tzinfo=UTC)
        if last and last < cutoff:
            app.status = Status.ghosted
            app.updated_at = now_utc()
            changed += 1
    return changed


def sync_messages_summary(
    db: Session,
    messages: list[ProviderMessage],
    provider: str,
    dry_run: bool = True,
    account_email: str | None = None,
    search_window: str = "sample",
) -> SyncSummary:
    summary = SyncSummary(
        provider=provider,
        account_email=account_email,
        search_window=search_window,
        messages_scanned=len(messages),
    )
    for msg in messages:
        if db.exec(select(EmailEvent).where(EmailEvent.message_id == msg.id)).first():
            summary.skipped_duplicates += 1
            continue
        result = classify_email(msg.subject, msg.sender, msg.snippet)
        company = company_from_sender(msg.sender)
        role = role_from_text(msg.subject, msg.snippet)
        received_at = parse_dt(msg.received_at) or now_utc()
        app = find_application(db, company, role, msg.thread_id)
        if not app:
            summary.applications_created += 1
            app = Application(
                company=company,
                role=role,
                source=provider,
                status=result.status,
                application_date=received_at if result.status == Status.applied else None,
                last_update_date=received_at,
                last_email_date=received_at,
                confidence=result.confidence,
            )
            db.add(app)
            db.flush()
        else:
            summary.applications_updated += 1
            if TERMINAL_RANK[result.status] >= TERMINAL_RANK[app.status]:
                app.status = result.status
                app.confidence = max(app.confidence, result.confidence)
            app.last_update_date = received_at
            app.last_email_date = max(app.last_email_date or received_at, received_at)
            app.updated_at = now_utc()

        event = EmailEvent(
            application_id=app.id,
            provider=provider,
            account_email=msg.account_email,
            message_id=msg.id,
            thread_id=msg.thread_id,
            sender=msg.sender,
            subject=msg.subject,
            received_at=received_at,
            event_type=result.event_type,
            status_inferred=result.status,
            confidence=result.confidence,
            reason=result.reason,
            snippet=(msg.snippet or "")[:500],
        )
        db.add(event)
        summary.events_detected += 1
        summary.lines.append(f"{company} | {role} | {result.status.value} | {result.reason}")
    apply_ghosting(db)
    if dry_run:
        db.rollback()
    else:
        db.commit()
    return summary


def sync_messages(db: Session, messages: list[ProviderMessage], provider: str, dry_run: bool = True) -> list[str]:
    return sync_messages_summary(db, messages, provider=provider, dry_run=dry_run).lines


def sync_provider_account(db: Session, account: ProviderAccount, dry_run: bool = False) -> SyncSummary:
    started = now_utc()
    window = gmail_after_before(account) or "all"
    try:
        if account.provider == "gmail":
            messages = GmailProvider().search_messages(window)
        elif account.provider == "outlook":
            raise NotImplementedError("Outlook sync is configured but not implemented yet")
        else:
            raise ValueError(f"Unsupported provider: {account.provider}")
        for msg in messages:
            msg.account_email = msg.account_email or account.account_email
        summary = sync_messages_summary(
            db,
            messages,
            provider=account.provider,
            dry_run=dry_run,
            account_email=account.account_email,
            search_window=window,
        )
        account.last_sync_at = started
        account.last_sync_status = "dry-run" if dry_run else "ok"
        account.last_sync_error = None
        db.add(account)
        db.commit()
        return summary
    except Exception as exc:
        account.last_sync_at = started
        account.last_sync_status = "error"
        account.last_sync_error = str(exc)
        db.add(account)
        db.commit()
        return SyncSummary(
            provider=account.provider,
            account_email=account.account_email,
            search_window=window,
            status="error",
            error=str(exc),
        )
