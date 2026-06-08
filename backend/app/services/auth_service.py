from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable
from uuid import uuid4

from fastapi import Depends, Header, HTTPException

from database.connection import get_connection
from database.init_db import utc_now_iso

PASSWORD_ITERATIONS = 210_000
JWT_TTL_MINUTES = int(os.getenv("HIREMIND_JWT_TTL_MINUTES", "30"))
JWT_ISSUER = os.getenv("HIREMIND_JWT_ISSUER", "hiremind")
JWT_AUDIENCE = os.getenv("HIREMIND_JWT_AUDIENCE", "hiremind-api")
JWT_SECRET = os.getenv("HIREMIND_JWT_SECRET") or os.getenv("SECRET_KEY") or secrets.token_urlsafe(64)
DEMO_ACCOUNTS: list[dict[str, str]] = []

class ConflictError(Exception):
    pass



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


def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _base64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("ascii"))


def _effective_role(role: str) -> str:
    normalized = (role or "").strip().lower()
    if normalized == "company":
        return "recruiter"
    return normalized


def _encode_jwt(payload: dict[str, Any]) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = _base64url_encode(json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    payload_b64 = _base64url_encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}"
    signature = hmac.new(
        JWT_SECRET.encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return f"{signing_input}.{_base64url_encode(signature)}"


def _decode_jwt(token: str) -> dict[str, Any]:
    try:
        header_b64, payload_b64, signature_b64 = token.split(".", 2)
        signing_input = f"{header_b64}.{payload_b64}"
        expected_signature = hmac.new(
            JWT_SECRET.encode("utf-8"),
            signing_input.encode("ascii"),
            hashlib.sha256,
        ).digest()
        actual_signature = _base64url_decode(signature_b64)
        if not hmac.compare_digest(expected_signature, actual_signature):
            raise ValueError("Invalid token signature.")

        header = json.loads(_base64url_decode(header_b64))
        payload = json.loads(_base64url_decode(payload_b64))
        if header.get("alg") != "HS256" or header.get("typ") != "JWT":
            raise ValueError("Unsupported token header.")

        now_ts = datetime.now(timezone.utc).timestamp()
        if float(payload.get("exp", 0)) <= now_ts:
            raise ValueError("Token has expired.")
        if payload.get("iss") != JWT_ISSUER:
            raise ValueError("Invalid token issuer.")
        if payload.get("aud") != JWT_AUDIENCE:
            raise ValueError("Invalid token audience.")
        return payload
    except Exception as exc:
        raise ValueError("Invalid authentication token.") from exc


def seed_demo_accounts() -> None:
    return None


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
            raise ConflictError("An account with this email already exists.")

        salt = secrets.token_bytes(16)
        now = utc_now_iso()
        user_id = str(uuid4())
        try:
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
        except Exception as exc:
            if "UNIQUE constraint failed" in str(exc) or "UniqueViolation" in exc.__class__.__name__:
                raise ConflictError("An account with this email already exists.") from exc
            raise
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
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=JWT_TTL_MINUTES)
    session_id = str(uuid4())

    with get_connection() as connection:
        user = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if user is None:
            raise ValueError("User not found.")
        payload = {
            "sub": user_id,
            "email": user["email"],
            "role": user["role"],
            "jti": uuid4().hex,
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
            "iss": JWT_ISSUER,
            "aud": JWT_AUDIENCE,
        }
        token = _encode_jwt(payload)
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
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
    payload = _decode_jwt(token)
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
        if row["id"] != payload.get("sub"):
            raise ValueError("Token subject mismatch.")
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
    return None


def extract_bearer_token(authorization: str | None = None, session_token: str | None = None) -> str:
    token = (session_token or "").strip()
    if not token and authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise ValueError("Authentication token is required.")
    return token


def require_current_user(
    authorization: str | None = Header(default=None),
    x_session_token: str | None = Header(default=None),
) -> AuthUser:
    try:
        token = extract_bearer_token(authorization, x_session_token)
        return get_current_user(token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


def require_role(*allowed_roles: str) -> Callable[..., AuthUser]:
    allowed = {_effective_role(role) for role in allowed_roles}

    def dependency(user: AuthUser = Depends(require_current_user)) -> AuthUser:
        if _effective_role(user.role) not in allowed and "any" not in allowed:
            raise HTTPException(status_code=403, detail="Insufficient role privileges.")
        return user

    return dependency


def effective_role(role: str) -> str:
    return _effective_role(role)
