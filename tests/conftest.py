"""Shared pytest fixtures."""

from __future__ import annotations

import pytest


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """Point the app at an empty SQLite file for one test."""
    path = tmp_path / "test.db"
    monkeypatch.setenv("RESUME_SEARCH_DB", str(path))
    from resume_search.auth import initialize_auth_db
    from resume_search.shortlists import initialize_shortlists_db

    initialize_auth_db()
    initialize_shortlists_db()
    return path
