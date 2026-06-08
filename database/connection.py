from __future__ import annotations

import os
import re
import sqlite3
import time
from contextlib import suppress
from functools import lru_cache
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import NullPool, QueuePool

# DB_PATH is relative to the project root
DB_PATH = Path(__file__).resolve().parents[1] / "database" / "recruitment.db"


def get_database_url() -> str:
    """Return the active database URL, defaulting to local SQLite for compatibility."""
    explicit_url = (
        os.getenv("HIREMIND_DATABASE_URL", "").strip()
        or os.getenv("DATABASE_URL", "").strip()
        or os.getenv("SQLALCHEMY_DATABASE_URL", "").strip()
    )
    if explicit_url:
        return explicit_url
    sqlite_path = DB_PATH.resolve().as_posix()
    return f"sqlite:///{sqlite_path}"


def get_database_backend() -> str:
    database_url = get_database_url().lower()
    return "postgresql" if database_url.startswith(("postgresql", "postgres://")) else "sqlite"


def _sanitize_database_url(url: str) -> str:
    if "@" not in url or "://" not in url:
        return url
    return re.sub(r"://([^:/]+):([^@]+)@", r"://\1:***@", url)


def _build_engine() -> Engine:
    database_url = get_database_url()
    if database_url.startswith("sqlite"):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        return create_engine(
            database_url,
            future=True,
            poolclass=NullPool,
            connect_args={"check_same_thread": False},
        )

    pool_size = int(os.getenv("HIREMIND_DB_POOL_SIZE", "10"))
    max_overflow = int(os.getenv("HIREMIND_DB_MAX_OVERFLOW", "20"))
    pool_timeout = int(os.getenv("HIREMIND_DB_POOL_TIMEOUT", "30"))
    pool_recycle = int(os.getenv("HIREMIND_DB_POOL_RECYCLE", "1800"))
    statement_timeout_ms = int(os.getenv("HIREMIND_DB_STATEMENT_TIMEOUT_MS", "5000"))
    connect_timeout = int(os.getenv("HIREMIND_DB_CONNECT_TIMEOUT_SECONDS", "5"))

    engine = create_engine(
        database_url,
        future=True,
        poolclass=QueuePool,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
        pool_recycle=pool_recycle,
        pool_pre_ping=True,
        connect_args={"connect_timeout": connect_timeout},
    )

    @event.listens_for(engine, "connect")
    def _apply_postgres_timeouts(dbapi_connection, connection_record):  # type: ignore[override]
        with suppress(Exception):
            with dbapi_connection.cursor() as cursor:
                cursor.execute(f"SET statement_timeout = {statement_timeout_ms}")
                cursor.execute("SET lock_timeout = 3000")

    return engine


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Return the shared SQLAlchemy engine instance."""
    return _build_engine()

class DatabaseConnection:
    """Compatibility wrapper supporting SQLite and PostgreSQL with the same API."""

    def __init__(self) -> None:
        self._backend = get_database_backend()
        self._sqlite_connection: sqlite3.Connection | None = None
        self._sqlalchemy_connection = None
        self._transaction = None
        self._entered = False

    def _ensure_connection(self) -> None:
        if self._backend == "sqlite":
            if self._sqlite_connection is not None:
                return
            DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            self._sqlite_connection = sqlite3.connect(DB_PATH)
            self._sqlite_connection.row_factory = sqlite3.Row
            self._sqlite_connection.execute("PRAGMA foreign_keys = ON")
            return

        if self._sqlalchemy_connection is not None:
            return
        self._sqlalchemy_connection = get_engine().connect()
        self._transaction = self._sqlalchemy_connection.begin()

    def __enter__(self):
        self._entered = True
        self._ensure_connection()
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc_type is None:
                self.commit()
            else:
                self.rollback()
        finally:
            self.close()
            self._entered = False
        return False

    def commit(self) -> None:
        if self._backend == "sqlite":
            if self._sqlite_connection is None:
                raise RuntimeError("Database connection not initialized.")
            self._sqlite_connection.commit()
            return

        if self._sqlalchemy_connection is None:
            raise RuntimeError("Database connection not initialized.")
        if self._transaction is None:
            return
        self._transaction.commit()
        self._transaction = None

    def rollback(self) -> None:
        if self._backend == "sqlite":
            if self._sqlite_connection is None:
                return
            self._sqlite_connection.rollback()
            return

        if self._sqlalchemy_connection is None:
            return
        if self._transaction is None:
            return
        self._transaction.rollback()
        self._transaction = None

    def close(self) -> None:
        if self._backend == "sqlite":
            if self._sqlite_connection is not None:
                self._sqlite_connection.close()
            self._sqlite_connection = None
            return

        if self._sqlalchemy_connection is not None:
            self._sqlalchemy_connection.close()
        self._sqlalchemy_connection = None
        self._transaction = None

    def execute(self, statement: str, params: Any | None = None):
        self._ensure_connection()
        params = () if params is None else params
        if self._backend == "sqlite":
            if self._sqlite_connection is None:
                raise RuntimeError("Database connection not initialized.")
            return self._sqlite_connection.execute(statement, params)

        if self._sqlalchemy_connection is None:
            raise RuntimeError("Database connection not initialized.")
        normalized = statement.replace("?", "%s")
        # In SQLAlchemy 2.0, exec_driver_sql returns a CursorResult.
        # Calling mappings() yields RowMapping objects which support string indexing.
        return self._sqlalchemy_connection.exec_driver_sql(normalized, params).mappings()

    def executescript(self, script: str):
        if self._backend == "sqlite":
            if self._sqlite_connection is None:
                raise RuntimeError("Database connection not initialized.")
            return self._sqlite_connection.executescript(script)

        # For Postgres, just use the raw DBAPI cursor to execute the whole script block
        if self._sqlalchemy_connection is None:
            raise RuntimeError("Database connection not initialized.")
        
        cursor = self._sqlalchemy_connection.connection.cursor()
        cursor.execute(script)
        return None


def get_connection() -> DatabaseConnection:
    """Return a transactional database connection wrapper."""
    return DatabaseConnection()


def _split_sql_script(script: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    in_single_quote = False
    in_double_quote = False

    for character in script:
        if character == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
        elif character == '"' and not in_single_quote:
            in_double_quote = not in_double_quote

        if character == ";" and not in_single_quote and not in_double_quote:
            statements.append("".join(current))
            current = []
        else:
            current.append(character)

    if current:
        statements.append("".join(current))

    return statements


def get_existing_columns(connection: DatabaseConnection, table_name: str) -> set[str]:
    """Return the existing column names for a table, independent of backend."""
    if get_database_backend() == "sqlite":
        rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
        return {row["name"] for row in rows}

    rows = connection.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = COALESCE(current_schema(), 'public')
          AND table_name = ?
        ORDER BY ordinal_position
        """,
        (table_name,),
    ).fetchall()
    return {row["column_name"] for row in rows}


def get_pool_metrics() -> dict[str, Any]:
    """Return pool status information for observability and readiness checks."""
    engine = get_engine()
    pool = getattr(engine, "pool", None)
    metrics: dict[str, Any] = {
        "backend": get_database_backend(),
        "database_url": _sanitize_database_url(get_database_url()),
    }

    if pool is None:
        return metrics

    for attribute in ("size", "checkedout", "overflow", "status"):
        if hasattr(pool, attribute):
            value = getattr(pool, attribute)
            try:
                metrics[f"pool_{attribute}"] = value() if callable(value) else value
            except Exception:
                metrics[f"pool_{attribute}"] = None

    return metrics


def ensure_database_ready() -> dict[str, Any]:
    """Run a readiness probe against the active database."""
    start = time.perf_counter()
    try:
        with get_connection() as connection:
            connection.execute("SELECT 1")
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        return {
            "ready": True,
            "backend": get_database_backend(),
            "latency_ms": elapsed_ms,
            "pool": get_pool_metrics(),
        }
    except Exception as exc:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        return {
            "ready": False,
            "backend": get_database_backend(),
            "latency_ms": elapsed_ms,
            "error": str(exc),
            "pool": get_pool_metrics(),
        }


def get_database_health() -> dict[str, Any]:
    """Return a health snapshot used by the API readiness endpoint."""
    health = ensure_database_ready()
    health["database_url"] = _sanitize_database_url(get_database_url())
    return health
