"""Tests for resume_search.shortlists and resume_search.db (temporary database)."""

from __future__ import annotations

import pytest

from resume_search.db import connect
from resume_search.shortlists import (
    add_to_shortlist,
    clear_user_data,
    count_shortlists,
    delete_shortlist,
    list_shortlists,
    remove_shortlist_item,
)


def _item(index=0, candidate="Ann Lee", score=0.5):
    return {"candidate": candidate, "score": score, "matched_skills": ["Python"],
            "dataset": "sample.csv", "original_index": index}


def test_add_and_list(temp_db):
    assert add_to_shortlist(1, "Python Developer", _item(0, score=0.4)) is True
    assert add_to_shortlist(1, "Python Developer", _item(1, "Bo", 0.9)) is True
    assert add_to_shortlist(1, "Python Developer", _item(0)) is False  # duplicate ignored
    (shortlist,) = list_shortlists(1)
    assert shortlist["name"] == "Python Developer"
    assert [item["candidate"] for item in shortlist["items"]] == ["Bo", "Ann Lee"]
    assert shortlist["items"][0]["matched_skills"] == "Python"


def test_blank_name_uses_default(temp_db):
    add_to_shortlist(1, "   ", _item())
    assert list_shortlists(1)[0]["name"] == "My shortlist"


def test_users_only_see_their_own_data(temp_db):
    add_to_shortlist(1, "Mine", _item())
    add_to_shortlist(2, "Theirs", _item())
    assert [s["name"] for s in list_shortlists(1)] == ["Mine"]
    assert count_shortlists(2) == 1
    theirs = list_shortlists(2)[0]
    delete_shortlist(1, theirs["id"])  # user 1 cannot delete user 2's list
    remove_shortlist_item(1, theirs["items"][0]["id"])
    assert len(list_shortlists(2)[0]["items"]) == 1


def test_delete_and_remove(temp_db):
    add_to_shortlist(1, "A", _item(0))
    add_to_shortlist(1, "A", _item(1))
    shortlist = list_shortlists(1)[0]
    remove_shortlist_item(1, shortlist["items"][0]["id"])
    assert len(list_shortlists(1)[0]["items"]) == 1
    delete_shortlist(1, shortlist["id"])
    assert list_shortlists(1) == []
    with connect() as connection:  # cascade removed the items too
        assert connection.execute("SELECT COUNT(*) FROM shortlist_items").fetchone()[0] == 0


def test_clear_user_data(temp_db):
    add_to_shortlist(1, "A", _item())
    add_to_shortlist(2, "B", _item())
    clear_user_data(1)
    assert count_shortlists(1) == 0
    assert count_shortlists(2) == 1


def test_connection_rolls_back_on_error(temp_db):
    with pytest.raises(RuntimeError), connect() as connection:
        connection.execute("INSERT INTO shortlists (user_id, name) VALUES (9, 'temp')")
        raise RuntimeError("boom")
    assert count_shortlists(9) == 0
