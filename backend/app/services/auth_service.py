from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from backend.app.services.recruitment_db import get_connection, utc_now_iso

SESSION_TTL_DAYS = 14
PASSWORD_ITERATIONS = 210_000
DEMO_ACCOUNTS = [
    {
        "email": "company@hiremind.ai",
        "password": "HireMind123!",
        "full_name": "HireMind Hiring Team",
        "role": "company",
        "company_name": "HireMind",
    },
    {
        "email": "candidate@hiremind.ai",
        "password": "HireMind123!",
        "full_name": "Alex Candidate",
        "role": "candidate",
        "company_name": "",
    },
]


@dataclass(slots=True)
class AuthUser:
    id: str
    email: str
    full_name: str
    role: str
    company_name: str
    is_active: bool
    created_at: str
    updated_at: str
    last_login_at: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role,
            "company_name": self.company_name,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_login_at": self.last_login_at,
        }


def _normalize_role(role: str) -> str:
    normalized = (role or "").strip().lower()
    if normalized not in {"candidate", "company"}:
        raise ValueError("Role must be either 'candidate' or 'company'.")
    return normalized


def _password_hash(password: str, salt: bytes) -> str:
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_ITERATIONS,
    )
    return base64.b64encode(digest).decode("ascii")


def _encode_salt(salt: bytes) -> str:
    return base64.b64encode(salt).decode("ascii")


def _decode_salt(encoded_salt: str) -> bytes:
    return base64.b64decode(encoded_salt.encode("ascii"))


def _row_to_user(row: sqlite3.Row | None) -> AuthUser | None:
    if row is None:
        return None
    return AuthUser(
        id=row["id"],
        email=row["email"],
        full_name=row["full_name"],
        role=row["role"],
        company_name=row["company_name"],
        is_active=bool(row["is_active"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        last_login_at=row["last_login_at"],
    )


def seed_demo_accounts() -> None:
    with get_connection() as connection:
        for account in DEMO_ACCOUNTS:
            existing = connection.execute(
                "SELECT id FROM users WHERE email = ?",
                (account["email"],),
            ).fetchone()
            if existing:
                continue
            create_user(
                email=account["email"],
                password=account["password"],
                full_name=account["full_name"],
                role=account["role"],
                company_name=account["company_name"],
                connection=connection,
            )


def create_user(
    *,
    email: str,
    password: str,
    full_name: str,
    role: str,
    company_name: str = "",
    connection: sqlite3.Connection | None = None,
) -> AuthUser:
    normalized_role = _normalize_role(role)
    normalized_email = email.strip().lower()
    if not normalized_email:
        raise ValueError("Email is required.")
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if not full_name.strip():
        raise ValueError("Full name is required.")
    if normalized_role == "company" and not company_name.strip():
        raise ValueError("Company name is required for company accounts.")

    close_connection = connection is None
    db = connection or get_connection()
    try:
        existing = db.execute(
            "SELECT id FROM users WHERE email = ?",
            (normalized_email,),
        ).fetchone()
        if existing:
            raise ValueError("An account with this email already exists.")

        salt = secrets.token_bytes(16)
        now = utc_now_iso()
        user_id = str(uuid4())
        db.execute(
            """
            INSERT INTO users (
                id, email, full_name, role, company_name,
                password_salt, password_hash, is_active,
                created_at, updated_at, last_login_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, NULL)
            """,
            (
                user_id,
                normalized_email,
                full_name.strip(),
                normalized_role,
                company_name.strip(),
                _encode_salt(salt),
                _password_hash(password, salt),
                now,
                now,
            ),
        )
        row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if close_connection:
            db.commit()
        return _row_to_user(row)
    finally:
        if close_connection:
            db.close()


def authenticate_user(email: str, password: str) -> AuthUser:
    normalized_email = email.strip().lower()
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE email = ?",
            (normalized_email,),
        ).fetchone()
        if row is None:
            raise ValueError("Invalid email or password.")
        if not row["is_active"]:
            raise ValueError("This account is disabled.")

        salt = _decode_salt(row["password_salt"])
        expected_hash = row["password_hash"]
        actual_hash = _password_hash(password, salt)
        if not hmac.compare_digest(expected_hash, actual_hash):
            raise ValueError("Invalid email or password.")

        now = utc_now_iso()
        connection.execute(
            "UPDATE users SET last_login_at = ?, updated_at = ? WHERE id = ?",
            (now, now, row["id"]),
        )
        connection.commit()
        refreshed = connection.execute(
            "SELECT * FROM users WHERE id = ?",
            (row["id"],),
        ).fetchone()
        return _row_to_user(refreshed)


def create_session(user_id: str) -> dict[str, str]:
    token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=SESSION_TTL_DAYS)
    session_id = str(uuid4())

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO auth_sessions (
                id, user_id, token_hash, created_at, expires_at, revoked_at
            ) VALUES (?, ?, ?, ?, ?, NULL)
            """,
            (
                session_id,
                user_id,
                token_hash,
                now.isoformat(),
                expires_at.isoformat(),
            ),
        )
        connection.commit()

    return {
        "session_id": session_id,
        "access_token": token,
        "token_type": "bearer",
        "expires_at": expires_at.isoformat(),
    }


def get_current_user(token: str) -> AuthUser:
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT u.*
            FROM auth_sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.token_hash = ?
              AND s.revoked_at IS NULL
              AND s.expires_at > ?
              AND u.is_active = 1
            """,
            (token_hash, now),
        ).fetchone()
        if row is None:
            raise ValueError("Invalid or expired session.")
        return _row_to_user(row)


def revoke_session(token: str) -> None:
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    now = utc_now_iso()
    with get_connection() as connection:
        connection.execute(
            "UPDATE auth_sessions SET revoked_at = ? WHERE token_hash = ?",
            (now, token_hash),
        )
        connection.commit()


def bootstrap_auth() -> None:
    seed_demo_accounts()
