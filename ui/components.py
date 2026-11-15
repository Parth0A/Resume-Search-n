"""Reusable HTML helpers.

Every helper that accepts text escapes it with :func:`html.escape`, so user
or resume text can never inject HTML through ``unsafe_allow_html``.
"""

from __future__ import annotations

import base64
from functools import lru_cache
from html import escape
from pathlib import Path

import streamlit as st

from resume_search.config import APP_NAME, APP_VERSION

ASSETS = Path(__file__).resolve().parent.parent / "assets"
ICON_SVG = ASSETS / "resume_search_icon.svg"
ICON_PNG = ASSETS / "resume_search_icon_512.png"
FAVICON = ASSETS / "resume_search_favicon_64.png"


def render(markup: str) -> None:
    """Render markup built by the helpers in this module (already escaped)."""
    st.markdown(markup, unsafe_allow_html=True)


@lru_cache(maxsize=1)
def icon_data_uri() -> str:
    """Return the app icon as a base64 data URI (SVG, falling back to the PNG)."""
    if ICON_SVG.exists():
        return "data:image/svg+xml;base64," + base64.b64encode(ICON_SVG.read_bytes()).decode("ascii")
    return "data:image/png;base64," + base64.b64encode(ICON_PNG.read_bytes()).decode("ascii")


def icon(size: int, css_class: str = "") -> str:
    """Return an <img> tag for the icon at a fixed square size."""
    return (
        f'<img class="rs-icon {escape(css_class)}" src="{icon_data_uri()}" width="{int(size)}" '
        f'height="{int(size)}" alt="{APP_NAME} logo">'
    )


def brand(icon_size: int, name_px: int, gap: int = 12) -> str:
    """Icon followed by the two-colour product name."""
    return (
        f'<div class="rs-brand" style="gap:{int(gap)}px">{icon(icon_size)}'
        f'<span class="rs-brand-name" style="font-size:{int(name_px)}px">'
        '<span class="rs-a">Resume</span> <span class="rs-b">Search</span></span></div>'
    )


def initials(name: str) -> str:
    """Up to two initials from a name or e-mail address."""
    words = [word for word in name.replace("@", " ").replace(".", " ").split() if word[:1].isalnum()]
    letters = "".join(word[0] for word in words[:2]).upper()
    return letters or "?"


def avatar(name: str, size: int = 40) -> str:
    """Round initials avatar."""
    return (
        f'<span class="rs-avatar" style="width:{int(size)}px;height:{int(size)}px;'
        f'font-size:{max(11, int(size * 0.36))}px" aria-hidden="true">{escape(initials(name))}</span>'
    )


def chip(text: str, kind: str = "neutral") -> str:
    """Pill chip. ``kind`` is matched, missing, neutral, review or role."""
    safe_kind = kind if kind in {"matched", "missing", "neutral", "review", "role"} else "neutral"
    return f'<span class="rs-chip rs-chip-{safe_kind}">{escape(str(text))}</span>'


def chips(items: list[str], kind: str, empty: str = "None") -> str:
    """A wrapping row of chips, or muted text when the list is empty."""
    if not items:
        return f'<span class="rs-muted">{escape(empty)}</span>'
    return '<div class="rs-chips">' + "".join(chip(item, kind) for item in items) + "</div>"


def relevance_bar(score: float) -> str:
    """8px bar with the score (two decimals) in bold on the right."""
    percent = max(0.0, min(1.0, float(score))) * 100
    return (
        f'<div class="rs-bar"><div class="rs-bar-track"><div class="rs-bar-fill" style="width:{percent:.1f}%">'
        f'</div></div><span class="rs-bar-value">{float(score):.2f}</span></div>'
    )


def score_ring(score: float) -> str:
    """Circular score indicator."""
    percent = max(0.0, min(1.0, float(score))) * 100
    return f'<div class="rs-ring" style="--pct:{percent:.1f}" role="img" aria-label="Score {score:.2f}"><span>{score:.2f}</span></div>'


def term_bars(terms: list[tuple[str, float]]) -> str:
    """Green bars for the terms behind a score, scaled to the largest one."""
    if not terms:
        return '<span class="rs-muted">No shared terms with the query.</span>'
    largest = max(value for _, value in terms) or 1.0
    rows = "".join(
        f'<div class="rs-term"><span>{escape(term)}</span><div class="rs-term-track">'
        f'<div class="rs-term-fill" style="width:{value / largest * 100:.1f}%"></div></div>'
        f'<span class="rs-term-value">{value:.3f}</span></div>'
        for term, value in terms
    )
    return f'<div class="rs-terms">{rows}</div>'


def card_header(number: int | str, title: str, description: str) -> str:
    """Numbered badge, title and muted description at the top of a card."""
    return (
        f'<div class="rs-card-header"><span class="rs-step-badge">{escape(str(number))}</span><div>'
        f'<div class="rs-card-title">{escape(title)}</div><div class="rs-card-desc">{escape(description)}</div></div></div>'
    )


def kpi_tiles(tiles: list[tuple[str, str]]) -> str:
    """Row of KPI tiles; the first tile uses the primary gradient."""
    parts = [
        f'<div class="rs-kpi{" primary" if position == 0 else ""}"><div class="rs-kpi-value">{escape(value)}</div>'
        f'<div class="rs-kpi-label">{escape(label)}</div></div>'
        for position, (value, label) in enumerate(tiles)
    ]
    return '<div class="rs-kpis">' + "".join(parts) + "</div>"


def info_strip(text: str) -> str:
    """Light indigo information strip."""
    return f'<div class="rs-info">{escape(text)}</div>'


def section_label(text: str) -> str:
    """Small uppercase label."""
    return f'<div class="rs-label">{escape(text)}</div>'


def empty_state(title: str, message: str) -> str:
    """Friendly empty state with the icon."""
    return f'<div class="rs-empty">{icon(56)}<strong>{escape(title)}</strong>{escape(message)}</div>'


def footer() -> str:
    """Small product footer with a 20px icon."""
    return f'<div class="rs-footer">{icon(20)}<span>{APP_NAME} · v{APP_VERSION} · MIT licence</span></div>'
