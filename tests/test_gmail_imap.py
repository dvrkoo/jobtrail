from __future__ import annotations

from datetime import UTC, date, datetime
from email.message import EmailMessage

import pytest

from jobtrail.providers.gmail_imap import (
    GmailImapClient,
    GmailImapProvider,
    get_password,
    in_window,
    message_from_bytes,
    parse_window,
    password_env_var,
    sanitize_email,
    window_bounds,
)
from jobtrail.models import ProviderAccount, SyncWindowType
from jobtrail.utils.windows import datetime_window


def raw_email(
    subject: str = "Application received",
    body: str = "Thank you for applying to our Engineer role.",
    date_header: str = "Mon, 1 Jun 2026 12:00:00 +0000",
) -> bytes:
    msg = EmailMessage()
    msg["From"] = "Jobs <jobs@example.com>"
    msg["To"] = "me@example.com"
    msg["Subject"] = subject
    msg["Date"] = date_header
    msg.set_content(body)
    return msg.as_bytes()


def test_password_env_name_and_lookup(monkeypatch) -> None:
    assert sanitize_email("Me+jobs@example.com") == "ME_JOBS_EXAMPLE_COM"
    name = password_env_var("Me+jobs@example.com")
    assert name == "JOBTRAIL_GMAIL_IMAP_PASSWORD_ME_JOBS_EXAMPLE_COM"
    monkeypatch.setenv(name, "app-password")
    assert get_password("Me+jobs@example.com") == "app-password"


def test_parse_window_uses_imap_dates() -> None:
    assert parse_window("after:2026/01/02 before:2026/02/03") == ["SINCE", "02-Jan-2026", "BEFORE", "03-Feb-2026"]
    assert parse_window("all") == ["ALL"]


def test_message_parsing_stores_snippet_not_body() -> None:
    msg = message_from_bytes("imap-1", "imap-1", raw_email(), "me@example.com")
    assert msg.subject == "Application received"
    assert msg.sender == "Jobs <jobs@example.com>"
    assert msg.snippet == "Thank you for applying to our Engineer role."
    assert msg.account_email == "me@example.com"


def test_missing_password_error(monkeypatch) -> None:
    monkeypatch.delenv(password_env_var("me@example.com"), raising=False)
    monkeypatch.setattr("jobtrail.providers.gmail_imap.get_password", lambda _: None)
    with pytest.raises(RuntimeError, match="Gmail IMAP password missing"):
        GmailImapProvider("me@example.com").search_messages()


def test_mocked_imap_filters_job_messages(monkeypatch) -> None:
    class FakeImap:
        def __init__(self, *_, **__):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return None

        def login(self, *_):
            return "OK", []

        def select(self, *_):
            return "OK", []

        def search(self, *_):
            return "OK", [b"1 2"]

        def fetch(self, raw_id, *_):
            subject = "Application received" if raw_id == b"1" else "Dinner plans"
            body = "Thank you for applying." if raw_id == b"1" else "See you at 7."
            return "OK", [(None, raw_email(subject, body))]

        def logout(self):
            return "BYE", []

    monkeypatch.setattr("jobtrail.providers.gmail_imap.get_password", lambda _: "pw")
    monkeypatch.setattr("imaplib.IMAP4_SSL", FakeImap)
    messages = GmailImapProvider("me@example.com").search_messages()
    assert [msg.subject for msg in messages] == ["Application received"]


def test_imap_aware_email_date_against_aware_window() -> None:
    msg = message_from_bytes("imap-1", "imap-1", raw_email(date_header="Mon, 1 Jun 2026 12:00:00 +0200"), "me@example.com")
    start, end = window_bounds("after:2026/05/24 before:2026/06/23")
    assert in_window(msg, start, end)


def test_imap_naive_email_date_against_aware_window() -> None:
    msg = message_from_bytes("imap-1", "imap-1", raw_email(date_header="Mon, 1 Jun 2026 12:00:00"), "me@example.com")
    start, end = window_bounds("after:2026/05/24 before:2026/06/23")
    assert in_window(msg, start, end)


def test_aware_email_date_against_absolute_date_window() -> None:
    account = ProviderAccount(
        provider="gmail_imap",
        account_email="me@example.com",
        sync_window_type=SyncWindowType.absolute,
        sync_start_date=date(2026, 6, 1),
        sync_end_date=date(2026, 6, 2),
    )
    msg = message_from_bytes("imap-1", "imap-1", raw_email(date_header="Mon, 1 Jun 2026 12:00:00 +0000"), "me@example.com")
    start, end = datetime_window(account)
    assert in_window(msg, start, end)


def test_missing_invalid_date_is_skipped(monkeypatch) -> None:
    class FakeImap:
        def __init__(self, *_, **__):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return None

        def login(self, *_):
            return "OK", []

        def select(self, *_):
            return "OK", []

        def search(self, *_):
            return "OK", [b"1"]

        def fetch(self, *_):
            return "OK", [(b"", raw_email(date_header="not a date"))]

        def logout(self):
            return "BYE", []

    monkeypatch.setattr("jobtrail.providers.gmail_imap.get_password", lambda _: "pw")
    monkeypatch.setattr("imaplib.IMAP4_SSL", FakeImap)
    assert GmailImapProvider("me@example.com").search_messages() == []


def test_internaldate_used_when_header_missing() -> None:
    msg = EmailMessage()
    msg["From"] = "Jobs <jobs@example.com>"
    msg["To"] = "me@example.com"
    msg["Subject"] = "Application received"
    msg.set_content("Thank you for applying.")
    parsed = message_from_bytes("imap-1", "imap-1", msg.as_bytes(), "me@example.com", internal_date=datetime(2026, 6, 1, tzinfo=UTC))
    assert parsed.received_at == "2026-06-01T00:00:00+00:00"


def test_gmail_imap_cleanup_called_after_success(monkeypatch) -> None:
    closed = []

    class FakeImap:
        def __init__(self, *_args, **_kwargs):
            self.sock = None

        def logout(self):
            closed.append("logout")

    monkeypatch.setattr("imaplib.IMAP4_SSL", FakeImap)
    with GmailImapClient():
        pass
    assert closed == ["logout"]


def test_gmail_imap_cleanup_called_after_failure(monkeypatch) -> None:
    closed = []

    class FakeImap:
        def __init__(self, *_args, **_kwargs):
            self.sock = None

        def logout(self):
            closed.append("logout")

    monkeypatch.setattr("imaplib.IMAP4_SSL", FakeImap)
    with pytest.raises(RuntimeError):
        with GmailImapClient():
            raise RuntimeError("boom")
    assert closed == ["logout"]
