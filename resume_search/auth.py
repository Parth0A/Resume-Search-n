"""Local SQLite account authentication.

* Passwords are hashed with PBKDF2-HMAC-SHA256 and a per-user random salt.
  The iteration count is stored per user; older, weaker hashes are re-hashed
  with the current count after a successful sign-in.
* After ``MAX_FAILED_LOGINS`` failures an e-mail address is locked for
  ``LOCKOUT_MINUTES``. Unknown e-mails and wrong passwords get the same error
  and take the same time, so attackers cannot tell which accounts exist.
* Only parameterised SQL is used. Nothing here logs e-mails or passwords.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from resume_search import config
from resume_search.db import connect

logger = logging.getLogger(__name__)

LEGACY_ITERATIONS = 310_000
"""Iteration count used by accounts created before per-user iterations existed."""

MAX_PASSWORD_LENGTH = 1024
INVALID_CREDENTIALS = "Email or password is incorrect."


class AccountLockedError(ValueError):
    """Raised when too many failed sign-ins locked the e-mail address."""


def initialize_auth_db() -> None:
    """Create or upgrade the account tables."""
    with connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('Recruiter', 'Job seeker')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS login_attempts (
                email TEXT PRIMARY KEY,
                failed_count INTEGER NOT NULL DEFAULT 0,
                locked_until TEXT
            );
            """
        )
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(users)")}
        if "iterations" not in columns:
            # Existing rows were hashed with LEGACY_ITERATIONS (310,000).
            connection.execute("ALTER TABLE users ADD COLUMN iterations INTEGER NOT NULL DEFAULT 310000")
        if "name" not in columns:
            connection.execute("ALTER TABLE users ADD COLUMN name TEXT NOT NULL DEFAULT ''")


def normalize_email(email: str) -> str:
    """Lower-case and validate an e-mail address.

    Raises:
        ValueError: for an invalid address.
    """
    normalized = (email or "").strip().lower()
    if len(normalized) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", normalized):
        raise ValueError("Enter a valid email address.")
    return normalized


def validate_password(password: str) -> None:
    """Check the password rules.

    Raises:
        ValueError: when the password is too short, too long or too common.
    """
    if len(password) < config.MIN_PASSWORD_LENGTH:
        raise ValueError(f"Use a password with at least {config.MIN_PASSWORD_LENGTH} characters.")
    if len(password) > MAX_PASSWORD_LENGTH:
        raise ValueError("That password is too long.")
    if password.lower() in config.COMMON_PASSWORDS:
        raise ValueError("That password is too common. Choose something harder to guess.")


def hash_password(password: str, salt: bytes, iterations: int = config.PBKDF2_ITERATIONS) -> str:
    """Return the hex PBKDF2-HMAC-SHA256 hash of ``password``."""
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations).hex()


def register_user(email: str, password: str, role: str, name: str = "") -> None:
    """Create an account.

    Raises:
        ValueError: for an invalid e-mail, weak password, bad role or duplicate account.
    """
    normalized_email = normalize_email(email)
    validate_password(password)
    if role not in config.ROLES:
        raise ValueError("Choose a valid account type.")
    clean_name = re.sub(r"\s+", " ", name or "").strip()[:80]
    salt = secrets.token_bytes(16)
    try:
        with connect() as connection:
            connection.execute(
                "INSERT INTO users (email, password_hash, salt, role, iterations, name) VALUES (?, ?, ?, ?, ?, ?)",
                (normalized_email, hash_password(password, salt), salt.hex(), role,
                 config.PBKDF2_ITERATIONS, clean_name),
            )
    except Exception as error:
        if "UNIQUE" in str(error):
            raise ValueError("An account with this email already exists. Sign in instead.") from error
        raise
    logger.info("Account created (role=%s)", role)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _locked_until(connection: Any, email: str) -> datetime | None:
    row = connection.execute("SELECT locked_until FROM login_attempts WHERE email = ?", (email,)).fetchone()
    if row is None or not row["locked_until"]:
        return None
    until = datetime.fromisoformat(row["locked_until"])
    return until if until > _now() else None


def _record_failure(connection: Any, email: str) -> None:
    row = connection.execute("SELECT failed_count FROM login_attempts WHERE email = ?", (email,)).fetchone()
    failed = (row["failed_count"] if row else 0) + 1
    locked_until = None
    if failed >= config.MAX_FAILED_LOGINS:
        locked_until = (_now() + timedelta(minutes=config.LOCKOUT_MINUTES)).isoformat()
        failed = 0
        logger.warning("Sign-in locked after repeated failures")
    connection.execute(
        """
        INSERT INTO login_attempts (email, failed_count, locked_until) VALUES (?, ?, ?)
        ON CONFLICT(email) DO UPDATE SET failed_count = excluded.failed_count,
                                         locked_until = excluded.locked_until
        """,
        (email, failed, locked_until),
    )


def authenticate_user(email: str, password: str) -> dict[str, Any] | None:
    """Return the user when the credentials are valid, otherwise None.

    Raises:
        AccountLockedError: while the e-mail address is locked.
        ValueError: for a malformed e-mail address.
    """
    normalized_email = normalize_email(email)
    with connect() as connection:
        locked = _locked_until(connection, normalized_email)
        if locked is not None:
            minutes = max(1, int((locked - _now()).total_seconds() // 60) + 1)
            raise AccountLockedError(
                f"Too many failed attempts. Try again in about {minutes} minute{'s' if minutes != 1 else ''}."
            )
        user = connection.execute(
            "SELECT id, email, password_hash, salt, role, iterations, name FROM users WHERE email = ?",
            (normalized_email,),
        ).fetchone()
        if user is None:
            # Spend the same time as a real check so unknown e-mails are not revealed by timing.
            hash_password(password, secrets.token_bytes(16))
            _record_failure(connection, normalized_email)
            return None
        expected = hash_password(password, bytes.fromhex(user["salt"]), user["iterations"])
        if not hmac.compare_digest(expected, user["password_hash"]):
            _record_failure(connection, normalized_email)
            return None
        connection.execute("DELETE FROM login_attempts WHERE email = ?", (normalized_email,))
        if user["iterations"] < config.PBKDF2_ITERATIONS:
            salt = secrets.token_bytes(16)
            connection.execute(
                "UPDATE users SET password_hash = ?, salt = ?, iterations = ? WHERE id = ?",
                (hash_password(password, salt), salt.hex(), config.PBKDF2_ITERATIONS, user["id"]),
            )
            logger.info("Password hash upgraded for user id %s", user["id"])
    return {"id": user["id"], "email": user["email"], "role": user["role"], "name": user["name"]}


def get_user(user_id: int) -> dict[str, Any] | None:
    """Return public account details (no password data) for ``user_id``."""
    with connect() as connection:
        row = connection.execute(
            "SELECT id, email, role, name, created_at FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    return dict(row) if row else None
