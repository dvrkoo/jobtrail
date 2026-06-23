from __future__ import annotations

import email
import imaplib
import logging
import os
import re
from datetime import datetime
from email.header import decode_header, make_header
from email.message import Message
from email.utils import parsedate_to_datetime

from jobtrail.classifiers.rules import RULES
from jobtrail.providers.base import MailProvider
from jobtrail.schemas import ProviderMessage
from jobtrail.utils.dates import ensure_aware_utc


HOST = "imap.gmail.com"
PORT = 993
SERVICE = "jobtrail-gmail-imap"
SOCKET_TIMEOUT_SECONDS = 20
LOGGER = logging.getLogger(__name__)


def sanitize_email(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "_", value).upper()


def password_env_var(email_address: str) -> str:
    return f"JOBTRAIL_GMAIL_IMAP_PASSWORD_{sanitize_email(email_address)}"


def keyring_name(email_address: str) -> str:
    return f"{SERVICE}:{email_address.lower()}"


def store_password(email_address: str, password: str) -> bool:
    try:
        import keyring

        keyring.set_password(SERVICE, keyring_name(email_address), password)
        return True
    except Exception:
        return False


def get_password(email_address: str) -> str | None:
    env_value = os.environ.get(password_env_var(email_address))
    if env_value:
        return env_value
    try:
        import keyring

        return keyring.get_password(SERVICE, keyring_name(email_address))
    except Exception:
        return None


def decode_mime(value: str | None) -> str | None:
    if not value:
        return None
    return str(make_header(decode_header(value)))


def body_snippet(message: Message, limit: int = 500) -> str:
    parts = message.walk() if message.is_multipart() else [message]
    for part in parts:
        if part.get_content_type() != "text/plain":
            continue
        payload = part.get_payload(decode=True)
        if not payload:
            continue
        charset = part.get_content_charset() or "utf-8"
        return re.sub(r"\s+", " ", payload.decode(charset, errors="replace")).strip()[:limit]
    return ""


def parse_email_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return ensure_aware_utc(parsedate_to_datetime(value))
    except (TypeError, ValueError):
        try:
            return ensure_aware_utc(datetime.fromisoformat(value.replace("Z", "+00:00")))
        except ValueError:
            return None


def parse_internaldate(fetch_meta: bytes | None) -> datetime | None:
    if not fetch_meta:
        return None
    match = re.search(rb'INTERNALDATE "([^"]+)"', fetch_meta)
    return parse_email_date(match.group(1).decode("ascii", errors="ignore")) if match else None


def message_from_bytes(
    message_id: str,
    thread_id: str,
    raw: bytes,
    account_email: str,
    internal_date: datetime | None = None,
) -> ProviderMessage:
    parsed = email.message_from_bytes(raw)
    received_at = parse_email_date(parsed.get("Date")) or internal_date
    if not received_at:
        raise ValueError("message has no parseable Date or INTERNALDATE")
    return ProviderMessage(
        id=message_id,
        thread_id=thread_id,
        sender=decode_mime(parsed.get("From")),
        subject=decode_mime(parsed.get("Subject")),
        snippet=body_snippet(parsed),
        received_at=ensure_aware_utc(received_at).isoformat(),
        account_email=account_email,
    )


def window_bounds(window_query: str | None) -> tuple[datetime | None, datetime | None]:
    if not window_query or window_query == "all":
        return None, None
    start = None
    end = None
    for name in ["after", "before"]:
        match = re.search(rf"{name}:(\d{{4}})/(\d{{2}})/(\d{{2}})", window_query)
        if not match:
            continue
        dt = ensure_aware_utc(datetime(int(match.group(1)), int(match.group(2)), int(match.group(3))))
        if name == "after":
            start = dt
        else:
            end = dt
    return start, end


def parse_window(window_query: str | None) -> list[str]:
    if not window_query or window_query == "all":
        return ["ALL"]
    terms = []
    for name, imap_name in [("after", "SINCE"), ("before", "BEFORE")]:
        match = re.search(rf"{name}:(\d{{4}})/(\d{{2}})/(\d{{2}})", window_query)
        if match:
            dt = datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
            terms.extend([imap_name, dt.strftime("%d-%b-%Y")])
    return terms or ["ALL"]


def looks_job_related(message: ProviderMessage) -> bool:
    text = f"{message.subject or ''} {message.sender or ''} {message.snippet or ''}".lower()
    return any(phrase in text for _, _, _, phrases in RULES for phrase in phrases)


def in_window(message: ProviderMessage, start: datetime | None, end: datetime | None) -> bool:
    received_at = parse_email_date(message.received_at)
    if not received_at:
        return False
    return (start is None or received_at >= start) and (end is None or received_at < end)


class GmailImapClient:
    def __init__(self, host: str = HOST, port: int = PORT, timeout: int = SOCKET_TIMEOUT_SECONDS):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.client: imaplib.IMAP4_SSL | None = None

    def __enter__(self) -> imaplib.IMAP4_SSL:
        self.client = imaplib.IMAP4_SSL(self.host, self.port, timeout=self.timeout)
        return self.client

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        client = self.client
        if not client:
            return
        sock = getattr(client, "sock", None)
        if sock:
            try:
                sock.settimeout(self.timeout)
            except OSError:
                pass
        try:
            client.logout()
        except Exception as exc:
            LOGGER.debug("Gmail IMAP logout skipped: %s", exc)
        finally:
            if sock:
                try:
                    sock.close()
                except OSError:
                    pass
            self.client = None


class GmailImapProvider(MailProvider):
    def __init__(self, account_email: str, password: str | None = None):
        self.account_email = account_email
        self.password = password

    def search_messages(self, window_query: str | None = None, max_messages: int | None = None) -> list[ProviderMessage]:
        password = self.password or get_password(self.account_email)
        if not password:
            raise RuntimeError(
                f"Gmail IMAP password missing. Store it in keyring or set {password_env_var(self.account_email)}."
            )
        with GmailImapClient() as client:
            client.login(self.account_email, password)
            client.select("INBOX")
            status, data = client.search(None, *parse_window(window_query))
            if status != "OK":
                return []
            messages = []
            start, end = window_bounds(window_query)
            for index, raw_id in enumerate(data[0].split()):
                if max_messages is not None and index >= max_messages:
                    break
                status, fetched = client.fetch(raw_id, "(RFC822 INTERNALDATE)")
                if status != "OK" or not fetched or not isinstance(fetched[0], tuple):
                    continue
                try:
                    msg = message_from_bytes(
                        message_id=f"imap-{raw_id.decode()}",
                        thread_id=f"imap-{raw_id.decode()}",
                        raw=fetched[0][1],
                        account_email=self.account_email,
                        internal_date=parse_internaldate(fetched[0][0]),
                    )
                except ValueError as exc:
                    LOGGER.warning("Skipping Gmail IMAP message %s: %s", raw_id.decode(), exc)
                    continue
                if in_window(msg, start, end) and looks_job_related(msg):
                    messages.append(msg)
            return messages

    def label_threads(self, thread_labels: dict[str, str], dry_run: bool = True) -> list[str]:
        raise NotImplementedError("Labels are only supported by the Gmail API provider for now.")
