from __future__ import annotations

import os


def demo_mode() -> bool:
    return os.environ.get("JOBTRAIL_UI_DEMO") == "1"
