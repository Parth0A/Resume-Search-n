"""Resume Search — Streamlit entry point.

Run with:  streamlit run app.py
"""

from __future__ import annotations

import logging

import streamlit as st

from resume_search.auth import initialize_auth_db
from resume_search.shortlists import initialize_shortlists_db
from ui import state
from ui.auth_view import render_login
from ui.components import FAVICON
from ui.header import render_header
from ui.theme import apply_theme

_PAGES = {
    state.PAGE_SCREEN: ("Screen candidates", "Upload a dataset, describe the role, review the ranked shortlist"),
    state.PAGE_SHORTLISTS: ("Saved shortlists", "Candidates you saved for each role"),
    state.PAGE_AI: ("AI tools", "Optional Gemini helpers that run only when you ask"),
    state.PAGE_PROFILE: ("My profile", "Your account details"),
    state.PAGE_PRIVACY: ("Privacy and data", "What is stored, what is shared and how to clear it"),
}


@st.cache_resource
def _initialise_database() -> bool:
    initialize_auth_db()
    initialize_shortlists_db()
    return True


def _render_page(page: str) -> None:
    # Screen modules are imported lazily so the login page loads quickly.
    if page == state.PAGE_SCREEN:
        from ui.results_view import render_results_card
        from ui.search_view import render_search_card
        from ui.upload_view import render_upload_card

        upload_col, search_col = st.columns(2, gap="medium")
        with upload_col:
            render_upload_card()
        with search_col:
            render_search_card()
        render_results_card()
    elif page == state.PAGE_SHORTLISTS:
        from ui.profile_view import render_shortlists_page

        render_shortlists_page()
    elif page == state.PAGE_AI:
        from ui.ai_view import render_ai_page

        render_ai_page()
    elif page == state.PAGE_PROFILE:
        from ui.profile_view import render_profile_page

        render_profile_page()
    else:
        from ui.profile_view import render_privacy_page

        render_privacy_page()


def main() -> None:
    """Configure the page and route to the right screen."""
    st.set_page_config(page_title="Resume Search", page_icon=str(FAVICON), layout="wide")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    apply_theme()
    _initialise_database()
    state.init_state()
    state.enforce_timeout()

    if state.current_user() is None:
        message = state.pop_flash()
        if message:
            st.info(message)
        render_login()
        return

    from ui.sidebar import render_sidebar

    render_sidebar()
    page = st.session_state[state.PAGE]
    if page not in _PAGES:
        page = state.PAGE_SCREEN
    title, subtitle = _PAGES[page]
    render_header(title, subtitle, show_steps=page == state.PAGE_SCREEN)
    message = state.pop_flash()
    if message:
        st.success(message)
    _render_page(page)


if __name__ == "__main__":
    main()
