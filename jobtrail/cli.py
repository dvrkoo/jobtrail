from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table
from sqlmodel import select

from jobtrail.config import AppConfig, config_exists, init_config, load_config, save_config, settings, update_config
from jobtrail.db import db_initialized, init_db, session
from jobtrail.models import Application, EmailEvent, ProviderAccount, Status
from jobtrail.providers.gmail import GmailProvider, load_sample
from jobtrail.services.export import export_csv, export_markdown
from jobtrail.services.labeling import thread_labels
from jobtrail.services.home import home_data, suggested_actions
from jobtrail.services.phrases import phrase
from jobtrail.services.providers import (
    add_provider_account,
    disable_or_delete,
    enabled_accounts,
    set_absolute_window,
    set_enabled,
    set_labels_enabled,
    set_relative_window,
)
from jobtrail.services.stats import stats as calc_stats
from jobtrail.services.sync import SyncSummary, sync_messages_summary, sync_provider_account
from jobtrail.utils.validation import positive_int, valid_email
from jobtrail.utils.windows import date_window, parse_relative_window

app = typer.Typer(invoke_without_command=True)
providers_app = typer.Typer(help="Manage provider accounts")
app.add_typer(providers_app, name="providers")
console = Console()


def first_startup_needed() -> bool:
    return not config_exists() or not db_initialized()


@app.callback()
def main(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand:
        return
    if first_startup_needed():
        run_onboarding()
    show_home()


@app.command()
def init() -> None:
    cfg = init_config()
    init_db(cfg.db_path)
    console.print(f"Initialized {cfg.db_path}")


@app.command()
def onboard() -> None:
    run_onboarding()


def run_onboarding() -> None:
    try:
        cfg = settings()
        console.print(Panel("JobTrail keeps your job search local and explainable.", title="Welcome"))
        console.print("Privacy: no full email bodies are stored by default. Emails are never deleted.")
        console.print(f"Config: {cfg.config_dir / 'config.toml'}")
        console.print(f"Data: {cfg.data_dir}")
        console.print(f"Tokens: {cfg.token_dir}")
        if config_exists() and not Confirm.ask("Existing config found. Edit it now?", default=False):
            init_db()
            console.print("Kept existing config.")
            return
        existing = load_config() if config_exists() else AppConfig()
        display_name = Prompt.ask("Display name", default=existing.display_name)
        greetings = Confirm.ask("Show motivational greetings on startup?", default=existing.motivational_greetings_enabled)
        tone = Prompt.ask("Motivational tone", choices=["calm", "aggressive", "funny", "professional"], default=existing.motivational_tone)
        while True:
            try:
                ghost_days = positive_int(IntPrompt.ask("Ghosting threshold in days", default=existing.ghosting_threshold_days))
                break
            except ValueError:
                console.print("Use a positive number, e.g. 30.")
        save_config(
            AppConfig(
                display_name=display_name,
                motivational_greetings_enabled=greetings,
                motivational_tone=tone,
                ghosting_threshold_days=ghost_days,
                default_export_format=existing.default_export_format,
                store_full_email_bodies=existing.store_full_email_bodies,
                created_at=existing.created_at,
            )
        )
        init_db()
        if Confirm.ask("Configure providers now?", default=True):
            while True:
                add_provider_interactive()
                if not Confirm.ask("Add another provider account?", default=False):
                    break
        console.print("Onboarding complete.")
        console.print(f"Config: {cfg.config_dir / 'config.toml'}")
        console.print(f"Data: {cfg.db_path}")
        console.print("Next: jobtrail sync --from-sample-json examples/sample_gmail_messages.json")
    except KeyboardInterrupt:
        console.print("Onboarding cancelled. Existing config was left unchanged.")


def show_home() -> None:
    init_db()
    config = load_config()
    greeting = f"Welcome back, {config.display_name}."
    if config.motivational_greetings_enabled:
        greeting += f" {phrase(config.motivational_tone)}"
    console.print(Panel(greeting, title="JobTrail"))
    with session() as db:
        data = home_data(db)
        show_home_tables(data)
    console.print("Suggested next actions:")
    for action in suggested_actions(data):
        console.print(f"  {action}")
    action = Prompt.ask("Action", choices=["sync", "list", "settings", "quit"], default="quit")
    if action == "sync":
        sync()
    elif action == "list":
        list_apps()
    elif action == "settings":
        settings_menu()


@app.command("settings")
def settings_menu() -> None:
    init_config()
    init_db()
    config = load_config()
    console.print(f"Display name: {config.display_name}")
    console.print(f"Greetings: {config.motivational_greetings_enabled} ({config.motivational_tone})")
    console.print(f"Ghosting threshold: {config.ghosting_threshold_days} days")
    console.print(f"Default export: {config.default_export_format}")
    choice = Prompt.ask(
        "Settings",
        choices=["name", "greetings", "tone", "ghosting", "export", "providers", "window", "labels", "quit"],
        default="quit",
    )
    if choice == "name":
        update_config(display_name=Prompt.ask("Display name", default=config.display_name))
    elif choice == "greetings":
        update_config(motivational_greetings_enabled=Confirm.ask("Enable greetings?", default=config.motivational_greetings_enabled))
    elif choice == "tone":
        update_config(motivational_tone=Prompt.ask("Tone", choices=["calm", "aggressive", "funny", "professional"], default=config.motivational_tone))
    elif choice == "ghosting":
        while True:
            try:
                days = positive_int(IntPrompt.ask("Ghosting threshold", default=config.ghosting_threshold_days))
                update_config(ghosting_threshold_days=days)
                break
            except ValueError:
                console.print("Use a positive number.")
    elif choice == "export":
        update_config(default_export_format=Prompt.ask("Default export", choices=["csv", "markdown"], default=config.default_export_format))
    elif choice == "providers":
        provider_list()
    elif choice == "window":
        provider_id = IntPrompt.ask("Provider account ID")
        window_kind = Prompt.ask("Window type", choices=["relative", "absolute", "all"], default="relative")
        with session() as db:
            account = db.get(ProviderAccount, provider_id)
            if not account:
                console.print("Provider not found")
            elif window_kind == "absolute":
                start = ask_date("Start date YYYY-MM-DD")
                end_text = ask_optional_date("End date YYYY-MM-DD, empty for today")
                set_absolute_window(account, start, date.fromisoformat(end_text) if end_text else None)
                db.add(account)
                db.commit()
                console.print("Saved")
            elif window_kind == "all":
                console.print("Saved" if set_relative_window(db, provider_id, "all available") else "Provider not found")
            else:
                window = Prompt.ask("Relative window", choices=["last 30 days", "last 90 days", "last 6 months", "last 12 months", "last 24 months"], default="last 12 months")
                console.print("Saved" if set_relative_window(db, provider_id, window) else "Provider not found")
    elif choice == "labels":
        provider_id = IntPrompt.ask("Provider account ID")
        enabled = Confirm.ask("Enable labels/categories?", default=True)
        with session() as db:
            console.print("Saved" if set_labels_enabled(db, provider_id, enabled) else "Provider not found")
    if choice not in {"providers", "window", "labels", "quit"}:
        console.print("Settings saved.")


@app.command()
def status() -> None:
    cfg = init_config()
    init_db(cfg.db_path)
    console.print(f"Config: {cfg.config_dir / 'config.toml'}")
    console.print(f"Database: {cfg.db_path} ({'ok' if db_initialized(cfg.db_path) else 'missing'})")
    with session() as db:
        show_status_tables(db)


def show_status_tables(db, brief: bool = False) -> None:
    data = calc_stats(db)
    stats_table = Table("Metric", "Value")
    keys = ["total", "pending", "interviews", "rejected", "ghosted"] if brief else data.keys()
    for key in keys:
        stats_table.add_row(str(key), str(data[key]))
    console.print(stats_table)
    accounts = db.exec(select(ProviderAccount).order_by(ProviderAccount.id)).all()
    provider_table = Table("ID", "Provider", "Account", "Enabled", "Window", "Last Sync")
    for account in accounts:
        start, end = date_window(account)
        window = "all" if not start and not end else f"{start or ''}..{end or ''}"
        provider_table.add_row(
            str(account.id),
            account.provider,
            account.account_email,
            str(account.enabled),
            window,
            account.last_sync_status or "never",
        )
    console.print(provider_table)
    if not accounts:
        console.print("Warning: no provider accounts configured. Run `jobtrail providers add`.")


def show_home_tables(data: dict[str, int | str | None]) -> None:
    stats_table = Table("Metric", "Value")
    for key in [
        "providers_count",
        "enabled_providers_count",
        "last_sync_summary",
        "total",
        "pending",
        "interviews",
        "assessments",
        "rejected",
        "offers",
        "ghosted",
    ]:
        stats_table.add_row(key, str(data[key]))
    console.print(stats_table)


def print_sync_summary(summary: SyncSummary) -> None:
    table = Table("Provider", "Window", "Scanned", "Events", "Created", "Updated", "Duplicates", "Status")
    table.add_row(
        f"{summary.provider}:{summary.account_email or 'sample'}",
        summary.search_window,
        str(summary.messages_scanned),
        str(summary.events_detected),
        str(summary.applications_created),
        str(summary.applications_updated),
        str(summary.skipped_duplicates),
        summary.error or summary.status,
    )
    console.print(table)


@app.command()
def sync(
    provider: str | None = None,
    account: Annotated[str | None, typer.Option()] = None,
    dry_run: bool = False,
    from_sample_json: Annotated[Path | None, typer.Option()] = None,
) -> None:
    init_config()
    init_db()
    if from_sample_json:
        messages = load_sample(from_sample_json)
        with session() as db:
            summary = sync_messages_summary(db, messages, provider=provider or "gmail", dry_run=dry_run)
        for line in summary.lines:
            console.print(line)
        print_sync_summary(summary)
        return
    with session() as db:
        accounts = enabled_accounts(db, provider=provider, account=account)
        if not accounts:
            console.print("No enabled provider accounts match. Run `jobtrail providers add`.")
            return
        for provider_account in accounts:
            summary = sync_provider_account(db, provider_account, dry_run=dry_run)
            if summary.error and provider_account.provider == "outlook":
                console.print("Outlook is configured but sync is planned. Use Gmail or sample JSON for now.")
            elif summary.error:
                console.print(f"Sync failed. Check credentials, then retry: {summary.error}")
            print_sync_summary(summary)


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
        if not db.exec(select(Application)).first():
            console.print("No applications to export. Run `jobtrail sync` first.")
            return
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


@providers_app.command("list")
def provider_list() -> None:
    init_db()
    with session() as db:
        accounts = db.exec(select(ProviderAccount).order_by(ProviderAccount.id)).all()
    table = Table("ID", "Provider", "Account", "Enabled", "Labels", "Window", "Last Sync", "Status")
    for item in accounts:
        start, end = date_window(item)
        window = "all" if not start and not end else f"{start or ''}..{end or ''}"
        table.add_row(
            str(item.id),
            item.provider,
            item.account_email,
            str(item.enabled),
            str(item.labels_enabled),
            window,
            str(item.last_sync_at or "never"),
            item.last_sync_status or "never",
        )
    console.print(table)
    if not accounts:
        console.print("No providers configured. Run `jobtrail providers add`.")


@providers_app.command("add")
def provider_add() -> None:
    init_config()
    init_db()
    add_provider_interactive()


def add_provider_interactive() -> ProviderAccount:
    provider = Prompt.ask("Provider", choices=["gmail", "outlook"], default="gmail")
    while True:
        email = Prompt.ask("Account email")
        if valid_email(email):
            break
        console.print("Enter an email like name@example.com.")
    labels = Confirm.ask("Enable labels/categories?", default=False)
    window_kind = Prompt.ask("Sync window type", choices=["relative", "absolute", "all"], default="relative")
    with session() as db:
        if window_kind == "absolute":
            start = ask_date("Start date YYYY-MM-DD")
            end_text = ask_optional_date("End date YYYY-MM-DD, empty for today")
            account = add_provider_account(db, provider, email, labels_enabled=labels, sync_choice="last 12 months")
            set_absolute_window(account, start, date.fromisoformat(end_text) if end_text else None)
            db.commit()
        elif window_kind == "all":
            account = add_provider_account(db, provider, email, labels_enabled=labels, sync_choice="all available")
        else:
            choice = Prompt.ask("Relative window", choices=["last 30 days", "last 90 days", "last 6 months", "last 12 months", "last 24 months", "all available"], default="last 12 months")
            parse_relative_window(choice)
            account = add_provider_account(db, provider, email, labels_enabled=labels, sync_choice=choice)
        if provider == "gmail":
            account.auth_state_path = str(Path("~/.local/share/jobtrail/tokens/gmail_token.json").expanduser())
            db.add(account)
            db.commit()
            console.print("Gmail account saved. OAuth starts on first sync if needed.")
            console.print("If you do not have credentials yet, add `credentials.json` in this directory.")
        else:
            console.print("Outlook account saved as a stub. Microsoft Graph auth is not implemented yet.")
        return account


def ask_date(prompt: str) -> date:
    while True:
        try:
            return date.fromisoformat(Prompt.ask(prompt))
        except ValueError:
            console.print("Use YYYY-MM-DD, e.g. 2026-01-31.")


def ask_optional_date(prompt: str) -> str:
    while True:
        value = Prompt.ask(prompt, default="")
        if not value:
            return ""
        try:
            date.fromisoformat(value)
            return value
        except ValueError:
            console.print("Use YYYY-MM-DD, e.g. 2026-01-31, or leave empty.")


@providers_app.command("remove")
def provider_remove(provider_account_id: int) -> None:
    init_db()
    console.print("Disabling is safer because it keeps sync history and settings.")
    if not Confirm.ask("Remove this provider account config?", default=False):
        console.print("Cancelled")
        return
    with session() as db:
        ok = disable_or_delete(db, provider_account_id, delete=True)
    console.print("Removed" if ok else "Provider account not found")


@providers_app.command("disable")
def provider_disable(provider_account_id: int) -> None:
    init_db()
    with session() as db:
        ok = set_enabled(db, provider_account_id, False)
    console.print("Disabled" if ok else "Provider account not found")


@providers_app.command("enable")
def provider_enable(provider_account_id: int) -> None:
    init_db()
    with session() as db:
        ok = set_enabled(db, provider_account_id, True)
    console.print("Enabled" if ok else "Provider account not found")


if __name__ == "__main__":
    app()
