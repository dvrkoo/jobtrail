from __future__ import annotations

from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

from jobtrail.config import settings


def engine(db_path: Path | None = None):
    path = db_path or settings().db_path
    path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{path}")


def init_db(db_path: Path | None = None) -> None:
    SQLModel.metadata.create_all(engine(db_path))


def session(db_path: Path | None = None) -> Session:
    return Session(engine(db_path))
