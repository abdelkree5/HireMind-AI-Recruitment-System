"""Copy the existing SQLite data set into a PostgreSQL target database."""
from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine, text

from database.connection import DB_PATH, get_database_url
from database.init_db import init_recruitment_db


TABLE_ORDER = [
    "users",
    "auth_sessions",
    "posted_jobs",
    "job_applications",
    "interview_sessions",
    "interview_turns",
    "recruiter_feedback",
    "dynamic_skill_weights",
    "agent_memory_stm",
    "agent_memory_ltm",
    "agent_episodes",
    "agent_traces",
    "agent_messages",
]


def _sqlite_source_url() -> str:
    source_path = Path(os.getenv("HIREMIND_SOURCE_SQLITE_PATH", str(DB_PATH))).resolve().as_posix()
    return f"sqlite:///{source_path}"


def migrate() -> None:
    target_url = get_database_url()
    if not target_url.startswith(("postgresql", "postgres://")):
        raise SystemExit(
            "DATABASE_URL or HIREMIND_DATABASE_URL must point to PostgreSQL for this migration script."
        )

    source_engine = create_engine(_sqlite_source_url(), future=True)
    target_engine = create_engine(target_url, future=True)

    init_recruitment_db()

    with source_engine.connect() as source_conn, target_engine.begin() as target_conn:
        for table_name in TABLE_ORDER:
            rows = source_conn.execute(text(f"SELECT * FROM {table_name}"))
            payload = [dict(row._mapping) for row in rows]
            if not payload:
                continue

            columns = list(payload[0].keys())
            column_sql = ", ".join(columns)
            bind_sql = ", ".join(f":{column}" for column in columns)
            insert_sql = text(f"INSERT INTO {table_name} ({column_sql}) VALUES ({bind_sql})")
            target_conn.execute(insert_sql, payload)

        target_conn.execute(
            text(
                "SELECT setval(pg_get_serial_sequence('interview_turns', 'id'), COALESCE((SELECT MAX(id) FROM interview_turns), 1), true)"
            )
        )


if __name__ == "__main__":
    migrate()