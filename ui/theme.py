"""Loads the single stylesheet into the page."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import streamlit as st

_STYLES = Path(__file__).with_name("styles.css")


@lru_cache(maxsize=1)
def _css() -> str:
    return _STYLES.read_text(encoding="utf-8")


def apply_theme() -> None:
    """Inject ui/styles.css (static file, no user content)."""
    st.markdown(f"<style>{_css()}</style>", unsafe_allow_html=True)
