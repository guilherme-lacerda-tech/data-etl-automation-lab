from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


def default_database_url(output_dir: Path) -> str:
    return os.getenv("DATABASE_URL", f"sqlite+pysqlite:///{output_dir / 'etl_lab.db'}")


def create_engine_for_url(database_url: str) -> Engine:
    options: dict[str, object] = {"future": True}
    if database_url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
        if ":memory:" in database_url:
            options["poolclass"] = StaticPool
    return create_engine(database_url, **options)


def create_session_factory(database_url: str):
    return sessionmaker(bind=create_engine_for_url(database_url), autoflush=False, expire_on_commit=False)


def database_backend(database_url: str) -> str:
    if database_url.startswith("postgresql"):
        return "postgresql"
    if database_url.startswith("sqlite"):
        return "sqlite"
    return "unknown"
