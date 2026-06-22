from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

from sqlmodel import Field, SQLModel


def now_utc() -> datetime:
    return datetime.now(UTC)


class Status(str, Enum):
    applied = "applied"
    assessment = "assessment"
    interview = "interview"
    rejected = "rejected"
    offer = "offer"
    pending = "pending"
    ghosted = "ghosted"
    unknown = "unknown"


class EventType(str, Enum):
    application_confirmation = "application_confirmation"
    rejection = "rejection"
    interview_request = "interview_request"
    assessment = "assessment"
    offer = "offer"
    recruiter_message = "recruiter_message"
    followup = "followup"
    generic_job_email = "generic_job_email"
    unknown = "unknown"


class Application(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    company: str = "unknown"
    role: str = "unknown"
    location: str | None = None
    source: str | None = None
    job_url: str | None = None
    status: Status = Status.unknown
    application_date: datetime | None = None
    last_update_date: datetime | None = None
    last_email_date: datetime | None = None
    confidence: float = 0.0
    notes: str | None = None
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)

class EmailEvent(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    application_id: int | None = Field(default=None, foreign_key="application.id")
    provider: str
    account_email: str | None = None
    message_id: str = Field(index=True)
    thread_id: str | None = Field(default=None, index=True)
    sender: str | None = None
    subject: str | None = None
    received_at: datetime | None = None
    event_type: EventType = EventType.unknown
    status_inferred: Status = Status.unknown
    confidence: float = 0.0
    reason: str = "No rule matched"
    snippet: str | None = None
    created_at: datetime = Field(default_factory=now_utc)

class ProviderAccount(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    provider: str
    account_email: str
    auth_state_path: str | None = None
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)
