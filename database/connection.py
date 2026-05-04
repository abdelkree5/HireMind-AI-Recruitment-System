from __future__ import annotations

import sqlite3
from pathlib import Path

# DB_PATH is relative to the project root
DB_PATH = Path(__file__).resolve().parents[1] / "database" / "recruitment.db"

def get_connection() -> sqlite3.Connection:
    """Returns a thread-safe connection to the recruitment database."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection
