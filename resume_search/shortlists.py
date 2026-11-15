"""Saved shortlists stored per user in SQLite.

Only a candidate label, score, matched skills and the dataset name are stored,
never the resume text. Every query is filtered by ``user_id`` so each user sees
only their own data.
"""

from __future__ import annotations

from typing import Any

from resume_search.db import connect


def initialize_shortlists_db() -> None:
    """Create the shortlist tables if they do not exist."""
    with connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS shortlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, name)
            );
            CREATE TABLE IF NOT EXISTS shortlist_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shortlist_id INTEGER NOT NULL REFERENCES shortlists(id) ON DELETE CASCADE,
                candidate TEXT NOT NULL,
                score REAL NOT NULL,
                matched_skills TEXT NOT NULL DEFAULT '',
                dataset TEXT NOT NULL DEFAULT '',
                original_index INTEGER NOT NULL,
                added_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(shortlist_id, dataset, original_index)
            );
            """
        )


def add_to_shortlist(user_id: int, shortlist_name: str, item: dict[str, Any]) -> bool:
    """Add a candidate to the named shortlist, creating it if needed.

    Returns:
        True when the candidate was added, False when it was already there.
    """
    name = shortlist_name.strip()[:120] or "My shortlist"
    with connect() as connection:
        connection.execute(
            "INSERT OR IGNORE INTO shortlists (user_id, name) VALUES (?, ?)", (user_id, name)
        )
        shortlist_id = connection.execute(
            "SELECT id FROM shortlists WHERE user_id = ? AND name = ?", (user_id, name)
        ).fetchone()["id"]
        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO shortlist_items
                (shortlist_id, candidate, score, matched_skills, dataset, original_index)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                shortlist_id,
                str(item["candidate"])[:200],
                float(item["score"]),
                ", ".join(item.get("matched_skills", []))[:500],
                str(item.get("dataset", ""))[:255],
                int(item["original_index"]),
            ),
        )
        return cursor.rowcount == 1


def list_shortlists(user_id: int) -> list[dict[str, Any]]:
    """Return the user's shortlists, newest first, each with its items."""
    with connect() as connection:
        shortlists = connection.execute(
            "SELECT id, name, created_at FROM shortlists WHERE user_id = ? ORDER BY id DESC",
            (user_id,),
        ).fetchall()
        result: list[dict[str, Any]] = []
        for shortlist in shortlists:
            items = connection.execute(
                """
                SELECT id, candidate, score, matched_skills, dataset, original_index, added_at
                FROM shortlist_items WHERE shortlist_id = ? ORDER BY score DESC, id
                """,
                (shortlist["id"],),
            ).fetchall()
            result.append({**dict(shortlist), "items": [dict(item) for item in items]})
    return result


def count_shortlists(user_id: int) -> int:
    """Return how many shortlists the user has."""
    with connect() as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS total FROM shortlists WHERE user_id = ?", (user_id,)
        ).fetchone()
    return int(row["total"])


def delete_shortlist(user_id: int, shortlist_id: int) -> None:
    """Delete one of the user's shortlists and its items."""
    with connect() as connection:
        connection.execute("DELETE FROM shortlists WHERE id = ? AND user_id = ?", (shortlist_id, user_id))


def remove_shortlist_item(user_id: int, item_id: int) -> None:
    """Remove one candidate from one of the user's shortlists."""
    with connect() as connection:
        connection.execute(
            """
            DELETE FROM shortlist_items WHERE id = ?
              AND shortlist_id IN (SELECT id FROM shortlists WHERE user_id = ?)
            """,
            (item_id, user_id),
        )


def clear_user_data(user_id: int) -> None:
    """Delete everything stored for the user except the account itself."""
    with connect() as connection:
        connection.execute("DELETE FROM shortlists WHERE user_id = ?", (user_id,))
