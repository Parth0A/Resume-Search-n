"""SQLite connection shared by accounts and shortlists."""

from __future__ import annotations

import contextlib
import os
import sqlite3
from collections.abc import Iterator
from pathlib import Path

from resume_search import config


def database_path() -> Path:
    """Return the configured database path (read at call time so tests can override it)."""
    return Path(os.getenv("RESUME_SEARCH_DB", str(config.DB_PATH)))


@contextlib.contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    """Open a connection, commit on success, roll back on error, always close."""
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    is_new = not path.exists()
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    if is_new:
        # Owner-only permissions where the OS supports POSIX modes.
        with contextlib.suppress(OSError):
            os.chmod(path, 0o600)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
