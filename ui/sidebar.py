"""Navy sidebar: brand, navigation and profile card."""

from __future__ import annotations

from html import escape

import streamlit as st

from ui import components, state

_WORKSPACE = (
    (state.PAGE_SCREEN, "Screen candidates"),
    (state.PAGE_SHORTLISTS, "Saved shortlists"),
    (state.PAGE_AI, "AI tools"),
)
_ACCOUNT = (
    (state.PAGE_PROFILE, "My profile"),
    (state.PAGE_PRIVACY, "Privacy and data"),
)


def _nav_item(page: str, label: str) -> None:
    active = st.session_state.get(state.PAGE) == page
    key = f"navactive_{page}" if active else f"nav_{page}"
    if st.button(label, key=key, use_container_width=True, type="tertiary"):
        state.go(page)
        st.rerun()


def render_sidebar() -> None:
    """Draw the sidebar for a signed-in user."""
    user = state.current_user()
    if user is None:
        return
    name = state.display_name(user)
    with st.sidebar:
        components.render(
            '<div class="rs-side-brand">'
            f'{components.icon(40)}<span class="rs-brand-name">Resume Search</span></div>'
        )
        components.render('<div class="rs-side-label">WORKSPACE</div>')
        for page, label in _WORKSPACE:
            _nav_item(page, label)
        components.render('<div class="rs-side-label">ACCOUNT</div>')
        for page, label in _ACCOUNT:
            _nav_item(page, label)
        with st.container(key="side_profile"):
            components.render(
                '<div class="rs-profile">'
                f"{components.avatar(name, 58)}"
                f'<span class="rs-profile-name">{escape(name)}</span>'
                f'<span class="rs-profile-email">{escape(user["email"])}</span>'
                f'{components.chip(user["role"], "role")}'
                "</div>"
            )
            if st.button("Sign out", key="signout", use_container_width=True):
                state.clear_session()
                st.rerun()
