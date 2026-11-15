"""My profile, Privacy and data, and Saved shortlists pages."""

from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

from resume_search.auth import get_user
from resume_search.config import SESSION_TIMEOUT_MINUTES
from resume_search.shortlists import (
    clear_user_data,
    count_shortlists,
    delete_shortlist,
    list_shortlists,
)
from ui import components, state


def render_profile_page() -> None:
    """Account details card."""
    user = state.current_user()
    record = get_user(user["id"]) or {}
    rows = [
        ("Name", state.display_name(user)),
        ("E-mail", user["email"]),
        ("Role", user["role"]),
        ("Member since", str(record.get("created_at", "—"))[:10]),
        ("Saved shortlists", str(count_shortlists(user["id"]))),
        ("Session timeout", f"{SESSION_TIMEOUT_MINUTES} minutes of inactivity"),
    ]
    with st.container(key="card_profile"):
        components.render(components.card_header("●", "My profile", "Your account on this device"))
        components.render(
            '<div class="rs-cand-head">'
            f"{components.avatar(state.display_name(user), 52)}"
            f'<div><div class="rs-cand-name">{escape(state.display_name(user))}</div>'
            f'<div class="rs-cand-meta">{escape(user["email"])}</div></div></div>'
        )
        st.table(pd.DataFrame(rows, columns=["Field", "Value"]).set_index("Field"))
        components.render(components.footer())


def render_privacy_page() -> None:
    """What is stored, what is sent to Gemini, and Clear my data."""
    user = state.current_user()
    with st.container(key="card_privacy"):
        components.render(components.card_header("●", "Privacy and data", "What Resume Search keeps and shares"))
        st.markdown(
            "**Stored on this device (SQLite database)**\n"
            "- Your account: e-mail, role, a salted PBKDF2 password hash, sign-in attempt counters.\n"
            "- Your saved shortlists: candidate label, score, matched skills and dataset file name. "
            "Resume text is never stored.\n\n"
            "**Kept only in memory for this browser session**\n"
            "- The uploaded dataset, the search index, results and AI outputs. They disappear when you sign out, "
            f"close the session or after {SESSION_TIMEOUT_MINUTES} minutes of inactivity.\n\n"
            "**Sent to Google Gemini (only when you press an AI button)**\n"
            "- The one selected resume (with e-mail addresses and phone numbers hidden) and your prompt text. "
            "Nothing is sent automatically, and the whole dataset is never sent."
        )
        st.divider()
        st.markdown("**Clear my data** deletes your saved shortlists and forgets the uploaded dataset, "
                    "results and AI outputs. Your account stays.")
        confirm = st.checkbox("I understand this cannot be undone.", key="confirm_clear")
        if st.button("Clear my data", key="clear_data", type="primary", disabled=not confirm):
            clear_user_data(user["id"])
            state.clear_working_data()
            st.session_state.pop("confirm_clear", None)
            state.flash("Your saved shortlists and session data were cleared.")
            st.rerun()


def render_shortlists_page() -> None:
    """The user's saved shortlists."""
    user = state.current_user()
    shortlists = list_shortlists(user["id"]) if state.is_recruiter() else []
    with st.container(key="card_shortlists"):
        components.render(components.card_header(
            "●", "Saved shortlists", "Candidates you shortlisted from search results"
        ))
        if not state.is_recruiter():
            components.render(components.empty_state("Recruiter feature", "Shortlists are available to recruiter accounts."))
            return
        if not shortlists:
            components.render(components.empty_state(
                "No shortlists yet", "Press Shortlist on a candidate in the results to save them here."
            ))
            return
        for shortlist in shortlists:
            count = len(shortlist["items"])
            label = f"{shortlist['name']} · {count} candidate{'s' if count != 1 else ''}"
            with st.expander(label, expanded=True):
                table = pd.DataFrame([
                    {"Candidate": item["candidate"], "Score": round(item["score"], 2),
                     "Matched skills": item["matched_skills"] or "—", "Dataset": item["dataset"],
                     "Added": str(item["added_at"])[:16]}
                    for item in shortlist["items"]
                ])
                st.dataframe(table, hide_index=True, use_container_width=True)
                export_col, delete_col = st.columns(2)
                with export_col:
                    st.download_button(
                        "Export CSV", data=table.to_csv(index=False), on_click="ignore",
                        file_name=f"shortlist_{shortlist['id']}.csv", mime="text/csv",
                        key=f"export_shortlist_{shortlist['id']}",
                    )
                with delete_col:
                    if st.button("Delete shortlist", key=f"delete_shortlist_{shortlist['id']}"):
                        delete_shortlist(user["id"], shortlist["id"])
                        state.flash(f"Deleted “{shortlist['name']}”.")
                        st.rerun()
