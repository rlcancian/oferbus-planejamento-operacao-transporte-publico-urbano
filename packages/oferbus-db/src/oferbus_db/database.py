from __future__ import annotations

import os
from functools import lru_cache

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

DEFAULT_DATABASE_URL = "postgresql+psycopg://oferbus:oferbus_local_dev@127.0.0.1:5432/oferbus"


def database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    return create_engine(
        database_url(),
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


def check_database() -> dict[str, str]:
    with get_engine().connect() as connection:
        row = connection.execute(
            text(
                "select current_database() as database_name, "
                "current_schema() as schema_name, "
                "current_setting('server_version') as server_version"
            )
        ).mappings().one()
        revision = connection.execute(
            text("select version_num from public.alembic_version limit 1")
        ).scalar_one_or_none()

    return {
        "database": str(row["database_name"]),
        "schema": str(row["schema_name"]),
        "server_version": str(row["server_version"]),
        "migration": str(revision or "unversioned"),
    }
