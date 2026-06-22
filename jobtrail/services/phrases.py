from __future__ import annotations

import random


PHRASES = {
    "calm": [
        "Small steps compound. Send one more application, then breathe.",
        "The goal is progress, not perfection.",
    ],
    "aggressive": [
        "Rejections are reps. Keep moving.",
        "Every no sharpens the next yes.",
    ],
    "funny": [
        "Another day, another ATS boss fight.",
        "Time to feed the spreadsheet goblin.",
    ],
    "professional": [
        "Consistency wins. Review the pipeline and take the next action.",
        "Your job search is a system. Keep the system moving.",
    ],
}


def phrase(tone: str, *, index: int | None = None) -> str:
    pack = PHRASES.get(tone, PHRASES["calm"])
    return pack[index % len(pack)] if index is not None else random.choice(pack)
