from jobtrail.classifiers.rules import classify_email
from jobtrail.models import EventType, Status


def test_classifier_rules() -> None:
    cases = [
        ("Application received", "Thank you for applying", EventType.application_confirmation, Status.applied),
        ("Update", "Unfortunately not moving forward", EventType.rejection, Status.rejected),
        ("Interview", "schedule a call", EventType.interview_request, Status.interview),
        ("Assessment", "coding challenge", EventType.assessment, Status.assessment),
        ("Offer", "pleased to offer", EventType.offer, Status.offer),
    ]
    for subject, snippet, event, status in cases:
        result = classify_email(subject, "jobs@example.com", snippet)
        assert result.event_type == event
        assert result.status == status
        assert result.confidence > 0
        assert result.reason.startswith("Matched phrase")
