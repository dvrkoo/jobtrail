from __future__ import annotations

import re


def valid_email(value: str) -> bool:
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value.strip()))


def positive_int(value: int) -> int:
    if value <= 0:
        raise ValueError("must be a positive integer")
    return value
