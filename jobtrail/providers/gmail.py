from __future__ import annotations

import json
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from jobtrail.config import settings
from jobtrail.providers.base import MailProvider
from jobtrail.schemas import ProviderMessage


SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
QUERY = " OR ".join(
    f'"{term}"'
    for term in [
        "thank you for applying",
        "application received",
        "we received your application",
        "unfortunately",
        "not moving forward",
        "interview",
        "technical assessment",
        "coding challenge",
        "recruiter",
        "talent acquisition",
        "offer",
    ]
)


class GmailProvider(MailProvider):
    def __init__(self, credentials_path: Path | None = None):
        self.credentials_path = credentials_path or Path("credentials.json")
        self._service = None

    @property
    def service(self):
        if self._service is None:
            self._service = build("gmail", "v1", credentials=self._credentials())
        return self._service

    def _credentials(self):
        cfg = settings()
        token_path = cfg.token_dir / "gmail_token.json"
        creds = Credentials.from_authorized_user_file(token_path, SCOPES) if token_path.exists() else None
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        cfg.token_dir.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json())
        return creds

    def search_messages(self, window_query: str | None = None) -> list[ProviderMessage]:
        q = f"({QUERY}) {window_query or ''}".strip()
        messages = self.service.users().messages().list(userId="me", q=q).execute().get("messages", [])
        return [self._message(item["id"]) for item in messages]

    def _message(self, message_id: str) -> ProviderMessage:
        raw = self.service.users().messages().get(userId="me", id=message_id, format="metadata").execute()
        headers = {h["name"].lower(): h["value"] for h in raw.get("payload", {}).get("headers", [])}
        received = headers.get("date")
        received_at = parsedate_to_datetime(received).isoformat() if received else datetime.now().isoformat()
        return ProviderMessage(
            id=raw["id"],
            thread_id=raw.get("threadId"),
            sender=headers.get("from"),
            subject=headers.get("subject"),
            snippet=raw.get("snippet"),
            received_at=received_at,
        )

    def label_threads(self, thread_labels: dict[str, str], dry_run: bool = True) -> list[str]:
        # ponytail: creates labels on demand; cache if Gmail quota becomes real pain.
        actions = []
        labels = self.service.users().labels().list(userId="me").execute().get("labels", []) if not dry_run else []
        ids = {label["name"]: label["id"] for label in labels}
        for thread_id, label in thread_labels.items():
            actions.append(f"{thread_id}: {label}")
            if dry_run:
                continue
            label_id = ids.get(label) or self.service.users().labels().create(
                userId="me", body={"name": label, "labelListVisibility": "labelShow"}
            ).execute()["id"]
            ids[label] = label_id
            self.service.users().threads().modify(
                userId="me", id=thread_id, body={"addLabelIds": [label_id]}
            ).execute()
        return actions


def load_sample(path: Path) -> list[ProviderMessage]:
    return [ProviderMessage.model_validate(item) for item in json.loads(path.read_text())]
