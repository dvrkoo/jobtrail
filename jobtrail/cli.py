from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table
from sqlmodel import select

from jobtrail.config import init_config
from jobtrail.db import init_db, session
from jobtrail.models import Application, EmailEvent, Status
from jobtrail.providers.gmail import GmailProvider, load_sample
from jobtrail.services.export import export_csv, export_markdown
from jobtrail.services.labeling import thread_labels
from jobtrail.services.stats import stats as calc_stats
from jobtrail.services.sync import sync_messages

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command()
def init() -> None:
    cfg = init_config()
    init_db(cfg.db_path)
    console.print(f"Initialized {cfg.db_path}")


@app.command()
def sync(
    provider: str = "gmail",
    dry_run: bool = False,
    from_sample_json: Annotated[Path | None, typer.Option()] = None,
) -> None:
    init_config()
    init_db()
    messages = load_sample(from_sample_json) if from_sample_json else GmailProvider().search_messages()
    with session() as db:
        lines = sync_messages(db, messages, provider=provider, dry_run=dry_run)
    for line in lines:
        console.print(line)
    console.print(f"{'Would save' if dry_run else 'Saved'} {len(lines)} events")


@app.command("list")
def list_apps(status: Status | None = None) -> None:
    with session() as db:
        query = select(Application).order_by(Application.last_email_date.desc())
        apps = db.exec(query).all()
    if status:
        apps = [item for item in apps if item.status == status]
    table = Table("ID", "Company", "Role", "Status", "Last Email")
    for item in apps:
        table.add_row(str(item.id), item.company, item.role, item.status.value, str(item.last_email_date or ""))
    console.print(table)


@app.command()
def show(application_id: int) -> None:
    with session() as db:
        app_row = db.get(Application, application_id)
        if not app_row:
            raise typer.Exit(f"No application {application_id}")
        events = db.exec(select(EmailEvent).where(EmailEvent.application_id == application_id)).all()
    console.print(f"[bold]{app_row.company}[/bold] - {app_row.role} ({app_row.status.value})")
    for event in events:
        console.print(f"{event.received_at}: {event.event_type.value} - {event.subject}")
        console.print(f"  {event.reason} ({event.confidence})")


@app.command()
def stats() -> None:
    with session() as db:
        data = calc_stats(db)
    for key, value in data.items():
        console.print(f"{key}: {value}")


@app.command()
def export(format: str = "csv") -> None:
    with session() as db:
        if format == "csv":
            console.print(export_csv(db), end="")
        elif format == "markdown":
            console.print(export_markdown(db), end="")
        else:
            raise typer.BadParameter("format must be csv or markdown")


@app.command("label-emails")
def label_emails(provider: str = "gmail", dry_run: bool = True, apply: bool = False) -> None:
    if provider != "gmail":
        raise typer.BadParameter("only gmail is implemented")
    with session() as db:
        labels = thread_labels(db)
    actions = GmailProvider().label_threads(labels, dry_run=not apply if apply else dry_run)
    for action in actions:
        console.print(action)
    console.print("Dry run" if not apply else "Applied")


if __name__ == "__main__":
    app()
