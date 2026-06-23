from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from jobtrail.config import init_config
from jobtrail.db import init_db, session
from jobtrail.providers.gmail import load_sample
from jobtrail.services.sync import sync_messages_summary


@dataclass
class UiLaunch:
    args: list[str]
    env: dict[str, str]


def prepare_demo(config_dir: Path, data_dir: Path, sample_path: Path) -> None:
    env = os.environ.copy()
    env["JOBTRAIL_CONFIG_DIR"] = str(config_dir)
    env["JOBTRAIL_DATA_DIR"] = str(data_dir)
    old_config = os.environ.get("JOBTRAIL_CONFIG_DIR")
    old_data = os.environ.get("JOBTRAIL_DATA_DIR")
    try:
        os.environ["JOBTRAIL_CONFIG_DIR"] = str(config_dir)
        os.environ["JOBTRAIL_DATA_DIR"] = str(data_dir)
        init_config()
        init_db()
        with session() as db:
            sync_messages_summary(db, load_sample(sample_path), provider="gmail", dry_run=False)
    finally:
        if old_config is None:
            os.environ.pop("JOBTRAIL_CONFIG_DIR", None)
        else:
            os.environ["JOBTRAIL_CONFIG_DIR"] = old_config
        if old_data is None:
            os.environ.pop("JOBTRAIL_DATA_DIR", None)
        else:
            os.environ["JOBTRAIL_DATA_DIR"] = old_data


def build_streamlit_launch(
    *,
    port: int,
    no_browser: bool,
    demo: bool,
    config_dir: Path | None = None,
    data_dir: Path | None = None,
) -> UiLaunch:
    app_path = Path(__file__).resolve().parents[1] / "ui" / "app.py"
    args = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.port",
        str(port),
        "--server.headless",
        "true" if no_browser else "false",
    ]
    env = os.environ.copy()
    env["JOBTRAIL_UI_DEMO"] = "1" if demo else "0"
    if config_dir:
        env["JOBTRAIL_CONFIG_DIR"] = str(config_dir)
    if data_dir:
        env["JOBTRAIL_DATA_DIR"] = str(data_dir)
    return UiLaunch(args=args, env=env)


def launch_ui(launch: UiLaunch) -> int:
    return subprocess.call(launch.args, env=launch.env)
