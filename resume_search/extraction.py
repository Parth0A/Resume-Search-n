"""Skill and experience extraction from resume text."""

from __future__ import annotations

import re

from resume_search.text import normalize_text

_EXPERIENCE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?<!\w)(\d{1,2})\s*(?:years?|yrs?)\s*(?:of\s*)?experience\b"),
)


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


def extract_skills(resume_text: str, skills: list[str]) -> list[str]:
    """Return the requested skills found in the resume, in request order."""
    resume = normalize_text(resume_text)
    found: list[str] = []
    seen: set[str] = set()
    for raw_skill in skills:
        skill = normalize_text(raw_skill)
        if not skill or skill in seen:
            continue
        seen.add(skill)
        pattern = r"(?<![a-z0-9])" + re.escape(skill) + r"(?![a-z0-9])"
        if re.search(pattern, resume):
            found.append(raw_skill.strip())
    return found


def extract_experience(resume_text: object) -> int | None:
    """Return the largest clearly stated number of years of experience, if any."""
    text = normalize_text(resume_text)
    best: int | None = None
    for pattern in _EXPERIENCE_PATTERNS:
        for match in pattern.finditer(text):
            value = int(match.group(1))
            if value > 0 and (best is None or value > best):
                best = value
    return best
