"""Local SQLite account authentication.

Passwords are salted and hashed with PBKDF2; plaintext passwords are never stored.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import sqlite3
from typing import Any

from resume_search import config
from resume_search.db import connect as _connect


def get_user(user_id: int) -> dict[str, Any] | None:
    """Return public account details (no password data) for ``user_id``."""
    with _connect() as connection:
        row = connection.execute(
            "SELECT id, email, role, created_at FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    return dict(row) if row else None


def initialize_auth_db() -> None:
    """Create the users table if it does not exist."""
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('Recruiter', 'Job seeker')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def _normalize_email(email: str) -> str:
    normalized = email.strip().lower()
    if len(normalized) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", normalized):
        raise ValueError("Enter a valid email address.")
    return normalized


def _hash_password(password: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 310_000).hex()


def register_user(email: str, password: str, role: str) -> None:
    """Create an account.

    Raises:
        ValueError: for an invalid e-mail, short password, bad role or duplicate.
    """
    normalized_email = _normalize_email(email)
    if len(password) < config.MIN_PASSWORD_LENGTH:
        raise ValueError("Use a password with at least 8 characters.")
    if role not in config.ROLES:
        raise ValueError("Choose a valid account type.")
    salt = secrets.token_bytes(16)
    try:
        with _connect() as connection:
            connection.execute(
                "INSERT INTO users (email, password_hash, salt, role) VALUES (?, ?, ?, ?)",
                (normalized_email, _hash_password(password, salt), salt.hex(), role),
            )
    except sqlite3.IntegrityError as error:
        raise ValueError("An account with this email already exists. Sign in instead.") from error


def authenticate_user(email: str, password: str) -> dict[str, Any] | None:
    """Return the user when the e-mail and password match, otherwise None."""
    normalized_email = _normalize_email(email)
    with _connect() as connection:
        user = connection.execute(
            "SELECT id, email, password_hash, salt, role FROM users WHERE email = ?",
            (normalized_email,),
        ).fetchone()
    if user is None:
        return None
    expected = _hash_password(password, bytes.fromhex(user["salt"]))
    if not hmac.compare_digest(expected, user["password_hash"]):
        return None
    return {"id": user["id"], "email": user["email"], "role": user["role"]}
