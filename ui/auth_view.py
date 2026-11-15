"""Sign-in and account-creation screen."""

from __future__ import annotations

import logging

import streamlit as st

from resume_search.auth import INVALID_CREDENTIALS, authenticate_user, register_user
from resume_search.config import ROLES
from ui import components, state

logger = logging.getLogger(__name__)

_BRAND_PANEL = """
<div class="rs-login-brand">
  <div class="rs-brand">{icon}<span class="rs-brand-name">Resume Search</span></div>
  <div>
    <div class="rs-login-headline">Find the right candidates in seconds.</div>
    <div class="rs-login-copy">Upload resumes, describe the role, and get a ranked, explainable shortlist.</div>
    <ul class="rs-login-points">
      <li><span class="rs-tick">✓</span>Ranks thousands of resumes in under a second</li>
      <li><span class="rs-tick">✓</span>Shows why each candidate matched</li>
      <li><span class="rs-tick">✓</span>Your data stays on your device</li>
    </ul>
  </div>
</div>
"""
_SIGN_IN = "Sign in"
_CREATE = "Create account"


def render_login() -> None:
    """Draw the two-column login panel and handle sign-in / sign-up."""
    components.render('<span class="rs-login-marker"></span>')
    with st.container(key="login_panel"):
        brand_col, form_col = st.columns(2, gap=None)
        with brand_col:
            components.render(_BRAND_PANEL.replace("{icon}", components.icon(48)))
        with form_col, st.container(key="login_form"):
            _render_form()


def _render_form() -> None:
    components.render(
        f'<div class="rs-login-mobile-brand">{components.brand(72, 24)}</div>'
        '<div class="rs-login-title">Welcome back</div>'
        '<div class="rs-login-sub">Sign in to continue to your workspace</div>'
    )
    mode = st.segmented_control(
        "Account access", [_SIGN_IN, _CREATE], default=_SIGN_IN, key="login_mode",
        label_visibility="collapsed", width="stretch",
    ) or _SIGN_IN
    creating = mode == _CREATE
    with st.form("auth_form", clear_on_submit=False, border=False):
        name = st.text_input("Full name", placeholder="Your name", max_chars=80) if creating else ""
        email = st.text_input("Email address", placeholder="you@company.com", autocomplete="email")
        password = st.text_input(
            "Password", type="password",
            placeholder="At least 8 characters" if creating else "Enter your password",
            autocomplete="new-password" if creating else "current-password",
        )
        role = st.selectbox("Account type", ROLES) if creating else None
        submitted = st.form_submit_button(mode, type="primary", use_container_width=True)
    if submitted:
        _submit(creating, email, password, role, name)
    components.render(
        '<div class="rs-login-foot">Protected with salted PBKDF2 hashing · locks after 5 failed attempts</div>'
    )


def _submit(creating: bool, email: str, password: str, role: str | None, name: str) -> None:
    try:
        with st.spinner("Signing you in…"):
            if creating:
                register_user(email, password, role or ROLES[0], name)
            user = authenticate_user(email, password)
    except ValueError as error:  # includes AccountLockedError; messages contain no user input
        st.error(str(error))
        return
    except Exception:
        logger.exception("Authentication failed unexpectedly")
        st.error("Sign-in could not be completed. Check local database access and try again.")
        return
    if user is None:
        st.error(INVALID_CREDENTIALS)
        return
    state.sign_in(user)
    st.rerun()
