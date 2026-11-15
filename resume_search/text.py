"""Text normalisation shared by every part of Resume Search.

There is exactly one normaliser (:func:`normalize_text`). Ranking, skill
matching and experience detection all use it, so the query and the resumes
are always treated the same way.
"""

from __future__ import annotations

import re

_WHITESPACE = re.compile(r"\s+")
_WORD = re.compile(r"\w")
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)")


def normalize_text(text: object) -> str:
    """Lower-case text and collapse whitespace; non-strings become ``""``."""
    if not isinstance(text, str):
        return ""
    return _WHITESPACE.sub(" ", text.lower().strip())


def has_words(text: object) -> bool:
    """Return True when the text contains at least one word character."""
    return bool(_WORD.search(normalize_text(text)))


def word_count(text: object) -> int:
    """Count whitespace-separated words in the text."""
    normalized = normalize_text(text)
    return len(normalized.split(" ")) if normalized else 0


def redact_contact_details(text: str) -> str:
    """Hide e-mail addresses and phone numbers (used by blind screening)."""
    if not isinstance(text, str):
        return ""
    without_email = _EMAIL.sub("[email hidden]", text)
    return _PHONE.sub(_phone_replacement, without_email)


def _phone_replacement(match: re.Match[str]) -> str:
    """Replace a phone-like match only when it has enough digits to be a phone."""
    digits = sum(character.isdigit() for character in match.group(0))
    return "[phone hidden]" if digits >= 9 else match.group(0)
