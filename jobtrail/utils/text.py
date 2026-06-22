from __future__ import annotations

import re
from email.utils import parseaddr


def normalize_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def normalize_key(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "", normalize_text(value)) or "unknown"


def company_from_sender(sender: str | None) -> str:
    name, email = parseaddr(sender or "")
    if name:
        return name.strip(' "')
    domain = email.split("@")[-1].split(">", 1)[0] if "@" in email else sender or "unknown"
    base = domain.split(".")[0] if domain else "unknown"
    return base.replace("-", " ").title() or "unknown"


def role_from_text(subject: str | None, snippet: str | None) -> str:
    texts = [subject or "", snippet or "", f"{subject or ''} {snippet or ''}"]
    patterns = [
        r"application for ([^\-.|:]+?)(?: position| role|$)",
        r"application to ([^\-.|:]+?)(?: position| role|$)",
        r"applied for ([^\-.|:]+?)(?: position| role|$)",
        r"(?:interview|assessment|offer) for ([^\-.|:]+?) position",
        r"([^\-.|:]+?) position",
    ]
    for text in texts:
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.I)
            if match:
                role = re.sub(r"\s+", " ", match.group(1)).strip(" .")
                return role[:80] or "unknown"
    return "unknown"
