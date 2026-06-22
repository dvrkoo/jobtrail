from __future__ import annotations

from pydantic import BaseModel

from jobtrail.models import EventType, Status


class ClassificationResult(BaseModel):
    event_type: EventType
    status: Status
    confidence: float
    reason: str


class ProviderMessage(BaseModel):
    id: str
    thread_id: str | None = None
    sender: str | None = None
    subject: str | None = None
    snippet: str | None = None
    received_at: str | None = None
    account_email: str | None = None
