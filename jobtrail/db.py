from __future__ import annotations

from pathlib import Path

from sqlalchemy import inspect, text
from sqlmodel import Session, SQLModel, create_engine

from jobtrail.config import settings


def engine(db_path: Path | None = None):
    path = db_path or settings().db_path
    path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{path}")


def init_db(db_path: Path | None = None) -> None:
    db_engine = engine(db_path)
    SQLModel.metadata.create_all(db_engine)
    upgrade_schema(db_engine)


def db_initialized(db_path: Path | None = None) -> bool:
    path = db_path or settings().db_path
    return path.exists() and "application" in inspect(engine(path)).get_table_names()


def upgrade_schema(db_engine) -> None:
    inspector = inspect(db_engine)
    if "provideraccount" not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns("provideraccount")}
    columns = {
        "enabled": "BOOLEAN DEFAULT 1",
        "labels_enabled": "BOOLEAN DEFAULT 0",
        "sync_window_type": "VARCHAR DEFAULT 'relative'",
        "sync_start_date": "DATE",
        "sync_end_date": "DATE",
        "relative_sync_value": "INTEGER DEFAULT 12",
        "relative_sync_unit": "VARCHAR DEFAULT 'months'",
        "last_sync_at": "DATETIME",
        "last_sync_status": "VARCHAR",
        "last_sync_error": "VARCHAR",
    }
    with db_engine.begin() as conn:
        for name, ddl in columns.items():
            if name not in existing:
                conn.execute(text(f"ALTER TABLE provideraccount ADD COLUMN {name} {ddl}"))


def session(db_path: Path | None = None) -> Session:
    return Session(engine(db_path))
