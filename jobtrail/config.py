from __future__ import annotations

import os
import tomllib
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel


class Settings(BaseModel):
    config_dir: Path
    data_dir: Path
    db_path: Path
    token_dir: Path
    ghost_after_days: int = 30


class AppConfig(BaseModel):
    display_name: str = "friend"
    motivational_greetings_enabled: bool = True
    motivational_tone: str = "calm"
    ghosting_threshold_days: int = 30
    default_export_format: str = "csv"
    store_full_email_bodies: bool = False
    created_at: str = ""
    updated_at: str = ""


def settings() -> Settings:
    config_dir = Path(os.environ.get("JOBTRAIL_CONFIG_DIR", "~/.config/jobtrail")).expanduser()
    data_dir = Path(os.environ.get("JOBTRAIL_DATA_DIR", "~/.local/share/jobtrail")).expanduser()
    cfg = config_dir / "config.toml"
    values = tomllib.loads(cfg.read_text()) if cfg.exists() else {}
    ghost_after_days = int(values.get("ghosting_threshold_days", values.get("ghost_after_days", 30)))
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
        save_config(AppConfig())
    return cfg


def config_path() -> Path:
    return settings().config_dir / "config.toml"


def config_exists() -> bool:
    return config_path().exists()


def load_config() -> AppConfig:
    path = config_path()
    if not path.exists():
        return AppConfig()
    values = tomllib.loads(path.read_text())
    if "ghost_after_days" in values and "ghosting_threshold_days" not in values:
        values["ghosting_threshold_days"] = values["ghost_after_days"]
    return AppConfig.model_validate(values)


def save_config(config: AppConfig) -> AppConfig:
    cfg = settings()
    cfg.config_dir.mkdir(parents=True, exist_ok=True)
    cfg.data_dir.mkdir(parents=True, exist_ok=True)
    cfg.token_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(UTC).isoformat()
    if not config.created_at:
        config.created_at = now
    config.updated_at = now
    lines = []
    for key, value in config.model_dump().items():
        if isinstance(value, bool):
            rendered = "true" if value else "false"
        elif isinstance(value, int):
            rendered = str(value)
        else:
            rendered = '"' + str(value).replace('"', '\\"') + '"'
        lines.append(f"{key} = {rendered}")
    config_path().write_text("\n".join(lines) + "\n")
    return config


def update_config(**changes: object) -> AppConfig:
    config = load_config()
    for key, value in changes.items():
        setattr(config, key, value)
    return save_config(config)
