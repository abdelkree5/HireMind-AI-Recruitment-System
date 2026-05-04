from __future__ import annotations

from datetime import datetime, timezone
from database.connection import get_connection

def init_recruitment_db() -> None:
    """Initializes the database schema and applies any pending migrations."""
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL,
                company_name TEXT NOT NULL DEFAULT '',
                password_salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_login_at TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

            CREATE TABLE IF NOT EXISTS auth_sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                token_hash TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                revoked_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_auth_sessions_user_id ON auth_sessions(user_id);
            CREATE INDEX IF NOT EXISTS idx_auth_sessions_token_hash ON auth_sessions(token_hash);

            CREATE TABLE IF NOT EXISTS posted_jobs (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                required_skills TEXT NOT NULL,
                responsibilities TEXT NOT NULL DEFAULT '[]',
                preferred_skills TEXT NOT NULL DEFAULT '[]',
                tools TEXT NOT NULL DEFAULT '[]',
                experience_level TEXT NOT NULL DEFAULT '',
                domain TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS job_applications (
                id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                candidate_name TEXT NOT NULL,
                candidate_headline TEXT NOT NULL,
                candidate_skills TEXT NOT NULL,
                match_score REAL NOT NULL,
                missing_skills TEXT NOT NULL,
                score_breakdown TEXT NOT NULL,
                feedback TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (job_id) REFERENCES posted_jobs(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_job_applications_job_id ON job_applications(job_id);
            CREATE INDEX IF NOT EXISTS idx_job_applications_match_score ON job_applications(match_score);
            CREATE INDEX IF NOT EXISTS idx_job_applications_created_at ON job_applications(created_at);

            CREATE TABLE IF NOT EXISTS interview_sessions (
                id TEXT PRIMARY KEY,
                application_id TEXT NOT NULL,
                job_id TEXT NOT NULL,
                candidate_name TEXT NOT NULL,
                status TEXT NOT NULL,
                total_questions INTEGER NOT NULL,
                current_question_index INTEGER NOT NULL,
                questions_json TEXT NOT NULL,
                candidate_profile_json TEXT NOT NULL DEFAULT '{}',
                answer_history_json TEXT NOT NULL DEFAULT '[]',
                difficulty_level TEXT NOT NULL DEFAULT 'medium',
                final_score REAL,
                final_recommendation TEXT,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                FOREIGN KEY (application_id) REFERENCES job_applications(id) ON DELETE CASCADE,
                FOREIGN KEY (job_id) REFERENCES posted_jobs(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS interview_turns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                question_index INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                candidate_answer TEXT NOT NULL,
                answer_score REAL NOT NULL,
                feedback TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES interview_sessions(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_interview_sessions_application_id ON interview_sessions(application_id);
            CREATE INDEX IF NOT EXISTS idx_interview_turns_session_id ON interview_turns(session_id);
            """
        )

        # Migrations
        _run_migrations(connection)

def _run_migrations(connection):
    existing_columns = {row["name"] for row in connection.execute("PRAGMA table_info(posted_jobs)").fetchall()}
    migrations = [
        ("responsibilities", "ALTER TABLE posted_jobs ADD COLUMN responsibilities TEXT NOT NULL DEFAULT '[]'"),
        ("preferred_skills", "ALTER TABLE posted_jobs ADD COLUMN preferred_skills TEXT NOT NULL DEFAULT '[]'"),
        ("tools", "ALTER TABLE posted_jobs ADD COLUMN tools TEXT NOT NULL DEFAULT '[]'"),
        ("experience_level", "ALTER TABLE posted_jobs ADD COLUMN experience_level TEXT NOT NULL DEFAULT ''"),
        ("domain", "ALTER TABLE posted_jobs ADD COLUMN domain TEXT NOT NULL DEFAULT ''"),
    ]
    for column_name, statement in migrations:
        if column_name not in existing_columns:
            connection.execute(statement)

    interview_columns = {row["name"] for row in connection.execute("PRAGMA table_info(interview_sessions)").fetchall()}
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
