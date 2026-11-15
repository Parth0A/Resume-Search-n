"""Skill and experience extraction from resume text."""

from __future__ import annotations

import re

from resume_search.config import SKILL_ALIASES
from resume_search.text import normalize_text

_YEARS = r"(?:years?|yrs?)"
_NUMBER = r"(?<![\w.])(\d{1,2})(?!\.\d)"  # one or two digits only, so years like 2019 never match
_EXPERIENCE_PATTERNS: tuple[re.Pattern[str], ...] = (
    # "5 years of experience", "5+ years experience", "5 years' professional experience"
    re.compile(_NUMBER + r"\s*\+?\s*" + _YEARS + r"['’]?\s+(?:of\s+)?(?:[a-z-]+\s+){0,3}?experience\b"),
    # "over 5 years", "more than 5 years", "at least 5+ years"
    re.compile(r"\b(?:over|more than|at least|nearly|almost|around|about)\s+" + _NUMBER + r"\s*\+?\s*" + _YEARS + r"\b"),
    # "experience of 5 years", "experience: 5+ years", "total experience - 5 yrs"
    re.compile(r"\bexperience\s*(?:of|:|-|–)?\s*(?:over\s+|more than\s+|about\s+)?" + _NUMBER + r"\s*\+?\s*" + _YEARS + r"\b"),
)
_MAX_YEARS = 50


def parse_skills(skills_text: str) -> list[str]:
    """Parse a comma-separated skill list, removing duplicates.

    Raises:
        ValueError: when the list contains a blank entry.
    """
    if not skills_text.strip():
        return []
    parsed: list[str] = []
    seen: set[str] = set()
    for item in skills_text.split(","):
        cleaned = item.strip()
        normalized = normalize_text(cleaned)
        if not normalized:
            raise ValueError("Skill list contains a blank entry.")
        if normalized not in seen:
            seen.add(normalized)
            parsed.append(cleaned)
    return parsed


def _alias_groups() -> dict[str, frozenset[str]]:
    """Map every known spelling to the full set of equivalent spellings."""
    groups: dict[str, set[str]] = {}
    for canonical, spellings in SKILL_ALIASES.items():
        members = {normalize_text(canonical), *(normalize_text(spelling) for spelling in spellings)}
        merged = set(members)
        for member in members:
            merged |= groups.get(member, set())
        for member in merged:
            groups[member] = merged
    return {spelling: frozenset(members) for spelling, members in groups.items()}


_ALIASES = _alias_groups()


def skill_spellings(skill: str) -> frozenset[str]:
    """All spellings that count as ``skill`` (itself plus configured aliases)."""
    normalized = normalize_text(skill)
    return _ALIASES.get(normalized, frozenset({normalized}))


def _skill_pattern(spelling: str) -> re.Pattern[str]:
    # A letter, digit, "+" or "#" right before or after means a different word:
    # "c" must not match "c++" / "c#", "java" must not match "javascript",
    # and "js" must not match the "js" inside "node.js".
    return re.compile(r"(?<![a-z0-9+#.])" + re.escape(spelling) + r"(?![a-z0-9+#])")


def extract_skills(resume_text: str, skills: list[str]) -> list[str]:
    """Return the requested skills found in the resume, in request order.

    A skill also matches through its aliases (for example "NodeJS" for "Node.js").
    """
    resume = normalize_text(resume_text)
    found: list[str] = []
    seen: set[str] = set()
    for raw_skill in skills:
        skill = normalize_text(raw_skill)
        if not skill or skill in seen:
            continue
        seen.add(skill)
        if any(_skill_pattern(spelling).search(resume) for spelling in skill_spellings(skill)):
            found.append(raw_skill.strip())
    return found


def extract_experience(resume_text: object) -> int | None:
    """Return the largest clearly stated number of years of experience, if any.

    Recognises "5 years of experience", "5+ years experience", "over 5 years",
    "experience of 5 years" and similar. Four-digit numbers (graduation or
    employment years) and durations without an experience cue ("project lasted
    2 years", "2 years ago") are ignored.
    """
    text = normalize_text(resume_text)
    best: int | None = None
    for pattern in _EXPERIENCE_PATTERNS:
        for match in pattern.finditer(text):
            value = int(match.group(1))
            if 0 < value <= _MAX_YEARS and (best is None or value > best):
                best = value
    return best
