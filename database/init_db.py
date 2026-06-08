from __future__ import annotations

from datetime import datetime, timezone

from database.connection import (
    get_connection,
    get_database_backend,
    get_existing_columns,
)
from database.schema_sql import build_schema_script

from dotenv import load_dotenv
load_dotenv()

def init_recruitment_db() -> None:
    """Initializes the database schema and applies any pending migrations."""
    with get_connection() as connection:
        connection.executescript(build_schema_script(get_database_backend()))

        # Migrations
        _run_migrations(connection)

def _run_migrations(connection):
    existing_columns = get_existing_columns(connection, "posted_jobs")
    migrations = [
        ("responsibilities", "ALTER TABLE posted_jobs ADD COLUMN responsibilities TEXT NOT NULL DEFAULT '[]'"),
        ("preferred_skills", "ALTER TABLE posted_jobs ADD COLUMN preferred_skills TEXT NOT NULL DEFAULT '[]'"),
        ("tools", "ALTER TABLE posted_jobs ADD COLUMN tools TEXT NOT NULL DEFAULT '[]'"),
        ("experience_level", "ALTER TABLE posted_jobs ADD COLUMN experience_level TEXT NOT NULL DEFAULT ''"),
        ("domain", "ALTER TABLE posted_jobs ADD COLUMN domain TEXT NOT NULL DEFAULT ''"),
        ("hiring_rules", "ALTER TABLE posted_jobs ADD COLUMN hiring_rules TEXT NOT NULL DEFAULT '{}'"),
    ]
    for column_name, statement in migrations:
        if column_name not in existing_columns:
            connection.execute(statement)

    interview_columns = get_existing_columns(connection, "interview_sessions")
    interview_migrations = [
        ("candidate_profile_json", "ALTER TABLE interview_sessions ADD COLUMN candidate_profile_json TEXT NOT NULL DEFAULT '{}'"),
        ("answer_history_json", "ALTER TABLE interview_sessions ADD COLUMN answer_history_json TEXT NOT NULL DEFAULT '[]'"),
        ("difficulty_level", "ALTER TABLE interview_sessions ADD COLUMN difficulty_level TEXT NOT NULL DEFAULT 'medium'"),
    ]
    for column_name, statement in interview_migrations:
        if column_name not in interview_columns:
            connection.execute(statement)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

if __name__ == "__main__":
    init_recruitment_db()
    print("Database initialized successfully.")
