"""Tests for resume_search.auth (temporary database, no real accounts)."""

from __future__ import annotations

import hashlib
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone

import pytest

from resume_search import auth, config
from resume_search.db import connect

PASSWORD = "Correct-Horse-42"


def test_register_and_login(temp_db):
    auth.register_user("Ann@Example.com ", PASSWORD, "Recruiter", "Ann  Lee")
    user = auth.authenticate_user("ann@example.com", PASSWORD)
    assert user == {"id": user["id"], "email": "ann@example.com", "role": "Recruiter", "name": "Ann Lee"}
    details = auth.get_user(user["id"])
    assert details["created_at"]
    assert "password_hash" not in details


def test_password_is_hashed_with_current_iterations(temp_db):
    auth.register_user("hash@example.com", PASSWORD, "Recruiter")
    with connect() as connection:
        row = connection.execute("SELECT password_hash, salt, iterations FROM users").fetchone()
    assert row["iterations"] == config.PBKDF2_ITERATIONS == 600_000
    assert PASSWORD not in row["password_hash"]
    expected = hashlib.pbkdf2_hmac("sha256", PASSWORD.encode(), bytes.fromhex(row["salt"]), 600_000).hex()
    assert row["password_hash"] == expected


def test_wrong_password_and_unknown_email_get_same_result(temp_db):
    auth.register_user("bo@example.com", PASSWORD, "Job seeker")
    assert auth.authenticate_user("bo@example.com", "wrong-password-1") is None
    assert auth.authenticate_user("nobody@example.com", PASSWORD) is None


def test_duplicate_email_rejected(temp_db):
    auth.register_user("dup@example.com", PASSWORD, "Recruiter")
    with pytest.raises(ValueError, match="already exists"):
        auth.register_user("DUP@example.com", PASSWORD, "Recruiter")


@pytest.mark.parametrize(
    ("email", "password", "role", "message"),
    [
        ("not-an-email", PASSWORD, "Recruiter", "valid email"),
        ("a@example.com", "short", "Recruiter", "at least 8"),
        ("a@example.com", "Password123", "Recruiter", "too common"),
        ("a@example.com", "x" * 2000, "Recruiter", "too long"),
        ("a@example.com", PASSWORD, "Admin", "account type"),
    ],
)
def test_registration_validation(temp_db, email, password, role, message):
    with pytest.raises(ValueError, match=message):
        auth.register_user(email, password, role)


def test_lockout_after_five_failures(temp_db):
    auth.register_user("lock@example.com", PASSWORD, "Recruiter")
    for _ in range(config.MAX_FAILED_LOGINS):
        assert auth.authenticate_user("lock@example.com", "wrong-password-1") is None
    with pytest.raises(auth.AccountLockedError, match="Too many failed attempts"):
        auth.authenticate_user("lock@example.com", PASSWORD)


def test_unknown_email_also_locks(temp_db):
    for _ in range(config.MAX_FAILED_LOGINS):
        auth.authenticate_user("ghost@example.com", "wrong-password-1")
    with pytest.raises(auth.AccountLockedError):
        auth.authenticate_user("ghost@example.com", "wrong-password-1")


def test_lock_expires(temp_db):
    auth.register_user("exp@example.com", PASSWORD, "Recruiter")
    past = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    with connect() as connection:
        connection.execute(
            "INSERT INTO login_attempts (email, failed_count, locked_until) VALUES (?, 0, ?)",
            ("exp@example.com", past),
        )
    assert auth.authenticate_user("exp@example.com", PASSWORD) is not None


def test_success_resets_failure_counter(temp_db):
    auth.register_user("reset@example.com", PASSWORD, "Recruiter")
    for _ in range(config.MAX_FAILED_LOGINS - 1):
        auth.authenticate_user("reset@example.com", "wrong-password-1")
    assert auth.authenticate_user("reset@example.com", PASSWORD) is not None
    for _ in range(config.MAX_FAILED_LOGINS - 1):
        auth.authenticate_user("reset@example.com", "wrong-password-1")
    assert auth.authenticate_user("reset@example.com", PASSWORD) is not None


def test_legacy_hash_is_upgraded_on_login(temp_db):
    salt = secrets.token_bytes(16)
    legacy_hash = hashlib.pbkdf2_hmac("sha256", PASSWORD.encode(), salt, auth.LEGACY_ITERATIONS).hex()
    with connect() as connection:
        connection.execute(
            "INSERT INTO users (email, password_hash, salt, role, iterations) VALUES (?, ?, ?, ?, ?)",
            ("old@example.com", legacy_hash, salt.hex(), "Recruiter", auth.LEGACY_ITERATIONS),
        )
    assert auth.authenticate_user("old@example.com", PASSWORD) is not None
    with connect() as connection:
        row = connection.execute("SELECT password_hash, iterations FROM users WHERE email = ?",
                                 ("old@example.com",)).fetchone()
    assert row["iterations"] == config.PBKDF2_ITERATIONS
    assert row["password_hash"] != legacy_hash
    assert auth.authenticate_user("old@example.com", PASSWORD) is not None


def test_initialize_upgrades_old_schema(tmp_path, monkeypatch):
    path = tmp_path / "old.db"
    monkeypatch.setenv("RESUME_SEARCH_DB", str(path))
    with sqlite3.connect(path) as connection:
        connection.execute(
            "CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT NOT NULL UNIQUE, "
            "password_hash TEXT NOT NULL, salt TEXT NOT NULL, role TEXT NOT NULL, "
            "created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
        )
    auth.initialize_auth_db()
    auth.initialize_auth_db()  # idempotent
    with connect() as connection:
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(users)")}
    assert {"iterations", "name"} <= columns
