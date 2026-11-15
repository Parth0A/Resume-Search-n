"""Session-state keys and helpers, kept in one place."""

from __future__ import annotations

import time
from typing import Any

import streamlit as st

from resume_search.config import ROLE_RECRUITER, SESSION_TIMEOUT_MINUTES

USER = "rs_user"
LAST_ACTIVITY = "rs_last_activity"
PAGE = "rs_page"
DATASET = "rs_dataset"
RESULTS = "rs_results"
SELECTED = "rs_selected"
AI_OUTPUTS = "rs_ai_outputs"
UPLOADER_VERSION = "rs_uploader_version"
FLASH = "rs_flash"

PAGE_SCREEN = "screen"
PAGE_CHECK = "check"
PAGE_SHORTLISTS = "shortlists"
PAGE_AI = "ai"
PAGE_PROFILE = "profile"
PAGE_PRIVACY = "privacy"


def enforce_timeout(now: float | None = None) -> bool:
    """Sign the user out after ``SESSION_TIMEOUT_MINUTES`` of inactivity.

    Returns:
        True when the session had expired and was cleared.
    """
    current = time.time() if now is None else now
    last = st.session_state.get(LAST_ACTIVITY)
    expired = (
        current_user() is not None
        and last is not None
        and current - last > SESSION_TIMEOUT_MINUTES * 60
    )
    if expired:
        clear_session()
        flash("You were signed out after 30 minutes of inactivity.")
    st.session_state[LAST_ACTIVITY] = current
    return expired


def init_state() -> None:
    """Create default session values once per browser session."""
    st.session_state.setdefault(USER, None)
    st.session_state.setdefault(PAGE, PAGE_SCREEN)
    st.session_state.setdefault(UPLOADER_VERSION, 0)
    st.session_state.setdefault(AI_OUTPUTS, {})


def current_user() -> dict[str, Any] | None:
    """The signed-in user, or None."""
    return st.session_state.get(USER)


def is_recruiter() -> bool:
    """True when the signed-in user is a recruiter."""
    user = current_user()
    return bool(user) and user["role"] == ROLE_RECRUITER


def display_name(user: dict[str, Any]) -> str:
    """The user's name, or a readable version of their e-mail address."""
    name = str(user.get("name") or "").strip()
    if name:
        return name
    local = str(user.get("email", "")).split("@")[0]
    return " ".join(part.capitalize() for part in local.replace("_", ".").split(".") if part) or "User"


def sign_in(user: dict[str, Any]) -> None:
    """Store the signed-in user and open the default page."""
    clear_session()
    st.session_state[USER] = user
    st.session_state[PAGE] = home_page(user)


def home_page(user: dict[str, Any]) -> str:
    """Recruiters start on Screen candidates, job seekers on Check my resume."""
    return PAGE_SCREEN if user["role"] == ROLE_RECRUITER else PAGE_CHECK


def allowed_pages(user: dict[str, Any]) -> tuple[str, ...]:
    """Pages a user may open; each role sees only its own tools."""
    if user["role"] == ROLE_RECRUITER:
        return (PAGE_SCREEN, PAGE_SHORTLISTS, PAGE_AI, PAGE_PROFILE, PAGE_PRIVACY)
    return (PAGE_CHECK, PAGE_AI, PAGE_PROFILE, PAGE_PRIVACY)


def clear_session() -> None:
    """Remove every value from the session (used by sign-out)."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_state()


def clear_working_data() -> None:
    """Forget the uploaded dataset, results and AI outputs, but stay signed in."""
    for key in (DATASET, RESULTS, SELECTED, "rs_my_resume", "rs_my_result"):
        st.session_state.pop(key, None)
    st.session_state[AI_OUTPUTS] = {}
    st.session_state[UPLOADER_VERSION] = st.session_state.get(UPLOADER_VERSION, 0) + 1


def go(page: str) -> None:
    """Navigate to a page."""
    st.session_state[PAGE] = page


def flash(message: str) -> None:
    """Queue a success message to show after the next rerun."""
    st.session_state[FLASH] = message


def pop_flash() -> str | None:
    """Return and clear the queued message."""
    return st.session_state.pop(FLASH, None)


def step_status() -> list[str]:
    """Return done/current/upcoming for Upload, Search, Results and AI tools."""
    has_data = st.session_state.get(DATASET) is not None
    has_results = st.session_state.get(RESULTS) is not None
    used_ai = bool(st.session_state.get(AI_OUTPUTS))
    done = [has_data, has_results, has_results and used_ai, used_ai]
    statuses: list[str] = []
    current_assigned = False
    for finished in done:
        if finished:
            statuses.append("done")
        elif not current_assigned:
            statuses.append("current")
            current_assigned = True
        else:
            statuses.append("upcoming")
    return statuses
