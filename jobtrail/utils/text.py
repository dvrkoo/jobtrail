from __future__ import annotations

import re
from email.utils import parseaddr


def normalize_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def normalize_key(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "", normalize_text(value)) or "unknown"


GENERIC_COMPANY_WORDS = {
    "careers",
    "jobs",
    "recruiting",
    "recruitment",
    "talent",
    "acquisition",
    "no reply",
    "noreply",
    "notifications",
    "hiring",
    "people",
}
ATS_DOMAINS = ("greenhouse.io", "lever.co", "workday", "smartrecruiters", "ashbyhq", "workable", "bamboohr")


def clean_company(value: str | None) -> str:
    text = re.sub(r"[<>\"']", " ", value or "")
    words = [word for word in re.split(r"\s+", text.strip()) if normalize_text(word) not in GENERIC_COMPANY_WORDS]
    return " ".join(words).strip(" .,-_") or "unknown"


def company_from_text(subject: str | None, snippet: str | None) -> str:
    text = f"{subject or ''} {snippet or ''}"
    patterns = [
        r"your application to ([A-Z][A-Za-z0-9 &.-]+?) for ",
        r"at ([A-Z][A-Za-z0-9 &.-]+?)(?:\.|,|$)",
        r"from ([A-Z][A-Za-z0-9 &.-]+?)(?:\.|,|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I)
        if match:
            return clean_company(match.group(1))[:80]
    return "unknown"


def company_from_sender(sender: str | None, subject: str | None = None, snippet: str | None = None) -> str:
    name, email = parseaddr(sender or "")
    domain = email.split("@")[-1].split(">", 1)[0].lower() if "@" in email else ""
    if any(ats in domain for ats in ATS_DOMAINS):
        company = company_from_text(subject, snippet)
        if company != "unknown":
            return company
    if name:
        cleaned = clean_company(name)
        if cleaned != "unknown":
            return cleaned
    domain = email.split("@")[-1].split(">", 1)[0] if "@" in email else sender or "unknown"
    base = domain.split(".")[0] if domain else "unknown"
    return clean_company(base.replace("-", " ").title()) or "unknown"


def role_from_text(subject: str | None, snippet: str | None) -> str:
    texts = [subject or "", snippet or "", f"{subject or ''} {snippet or ''}"]
    patterns = [
        r"application for ([^\-.|:]+?)(?: position| role|$)",
        r"your application for ([^\-.|:]+?)(?: position| role|$)",
        r"your application to [^\-.|:]+? for ([^\-.|:]+?)(?: position| role|$)",
        r"application to ([^\-.|:]+?)(?: position| role|$)",
        r"applied for ([^\-.|:]+?)(?: position| role|$)",
        r"you applied to ([^\-.|:]+?)(?: position| role|$)",
        r"regarding your application for ([^\-.|:]+?)(?: position| role|$)",
        r"invitation for ([^\-.|:]+?) interview",
        r"next steps for ([^\-.|:]+?)(?: position| role|$)",
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
