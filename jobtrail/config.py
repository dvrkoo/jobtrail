from __future__ import annotations

import os
import tomllib
from pathlib import Path

from pydantic import BaseModel


class Settings(BaseModel):
    config_dir: Path
    data_dir: Path
    db_path: Path
    token_dir: Path
    ghost_after_days: int = 30


def settings() -> Settings:
    config_dir = Path(os.environ.get("JOBTRAIL_CONFIG_DIR", "~/.config/jobtrail")).expanduser()
    data_dir = Path(os.environ.get("JOBTRAIL_DATA_DIR", "~/.local/share/jobtrail")).expanduser()
    cfg = config_dir / "config.toml"
    values = tomllib.loads(cfg.read_text()) if cfg.exists() else {}
    ghost_after_days = int(values.get("ghost_after_days", 30))
    return Settings(
        config_dir=config_dir,
        data_dir=data_dir,
        db_path=data_dir / "jobtrail.db",
        token_dir=data_dir / "tokens",
        ghost_after_days=ghost_after_days,
    )


def init_config() -> Settings:
    cfg = settings()
    cfg.config_dir.mkdir(parents=True, exist_ok=True)
    cfg.data_dir.mkdir(parents=True, exist_ok=True)
    cfg.token_dir.mkdir(parents=True, exist_ok=True)
    path = cfg.config_dir / "config.toml"
    if not path.exists():
        path.write_text("ghost_after_days = 30\n")
    return cfg
