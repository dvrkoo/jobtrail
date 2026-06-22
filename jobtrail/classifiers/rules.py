from __future__ import annotations

from jobtrail.models import EventType, Status
from jobtrail.schemas import ClassificationResult
from jobtrail.utils.text import normalize_text


RULES = [
    (EventType.offer, Status.offer, 0.95, ["pleased to offer", "offer", "congratulations"]),
    (
        EventType.rejection,
        Status.rejected,
        0.9,
        [
            "unfortunately",
            "not moving forward",
            "decided to proceed with other candidates",
            "we will not be moving forward",
        ],
    ),
    (
        EventType.assessment,
        Status.assessment,
        0.85,
        ["assessment", "coding challenge", "technical test", "take-home"],
    ),
    (
        EventType.interview_request,
        Status.interview,
        0.85,
        ["interview", "schedule a call", "meet with the team"],
    ),
    (
        EventType.application_confirmation,
        Status.applied,
        0.85,
        ["thank you for applying", "application received", "we received your application"],
    ),
    (EventType.recruiter_message, Status.pending, 0.65, ["recruiter", "talent acquisition"]),
]


def classify_email(subject: str | None, sender: str | None, snippet: str | None) -> ClassificationResult:
    text = normalize_text(f"{subject or ''} {sender or ''} {snippet or ''}")
    for event_type, status, confidence, phrases in RULES:
        for phrase in phrases:
            if phrase in text:
                return ClassificationResult(
                    event_type=event_type,
                    status=status,
                    confidence=confidence,
                    reason=f"Matched phrase: {phrase}",
                )
    return ClassificationResult(
        event_type=EventType.generic_job_email,
        status=Status.unknown,
        confidence=0.3,
        reason="No job status phrase matched",
    )
