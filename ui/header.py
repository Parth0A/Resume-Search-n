"""App header: page title, step tracker and signed-in user."""

from __future__ import annotations

from html import escape

from ui import components, state

_STEPS = ("Upload", "Search", "Results", "AI tools")


def _step_tracker() -> str:
    parts: list[str] = []
    for number, (label, status) in enumerate(zip(_STEPS, state.step_status(), strict=True), start=1):
        if parts:
            parts.append('<span class="rs-step-sep"></span>')
        marker = "✓" if status == "done" else str(number)
        parts.append(
            f'<div class="rs-step {status}" aria-label="{label}: {status}">'
            f'<span class="rs-step-dot">{marker}</span>{label}</div>'
        )
    return '<div class="rs-steps">' + "".join(parts) + "</div>"


def render_header(title: str, subtitle: str, show_steps: bool = False) -> None:
    """Draw the white header bar at the top of the main area."""
    user = state.current_user() or {}
    name = state.display_name(user) if user else ""
    components.render(
        '<div class="rs-header">'
        f'<div class="rs-header-title"><div class="rs-header-h1">{escape(title)}</div><div class="rs-header-sub">{escape(subtitle)}</div></div>'
        f"{_step_tracker() if show_steps else ''}"
        f'<div class="rs-user"><span class="rs-user-name">{escape(name)}</span>{components.avatar(name, 40)}</div>'
        "</div>"
    )
