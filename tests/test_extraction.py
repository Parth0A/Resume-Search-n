"""Tests for resume_search.extraction."""

from __future__ import annotations

import pytest

from resume_search.extraction import extract_experience, extract_skills, parse_skills


class TestParseSkills:
    def test_parses_comma_separated_skills(self):
        assert parse_skills("Python, SQL, Git") == ["Python", "SQL", "Git"]

    def test_deduplicates_skills(self):
        assert parse_skills("Python, python, Git") == ["Python", "Git"]

    def test_trims_whitespace(self):
        assert parse_skills(" Python , SQL ") == ["Python", "SQL"]

    def test_returns_empty_for_blank_input(self):
        assert parse_skills("") == []
        assert parse_skills("   ") == []

    def test_rejects_blank_entries(self):
        with pytest.raises(ValueError):
            parse_skills("Python, , Git")

    def test_rejects_blank_after_normalization(self):
        with pytest.raises(ValueError):
            parse_skills("Python, ,")


class TestExtractSkills:
    def test_finds_exact_skills(self):
        assert extract_skills("Experienced Python and SQL developer.", ["Python", "SQL"]) == ["Python", "SQL"]

    def test_missing_skill_not_returned(self):
        assert extract_skills("Java backend developer.", ["Python", "SQL"]) == []

    def test_uses_word_boundary_to_reduce_substring_errors(self):
        matched = extract_skills("JavaScript developer with Node experience.", ["Java", "JavaScript"])
        assert "Java" not in matched
        assert "JavaScript" in matched

    def test_deduplicates_detected_skills(self):
        matched = extract_skills("Python developer familiar with python tooling.", ["Python", "python"])
        assert matched.count("Python") == 1

    def test_handles_empty_skill_list(self):
        assert extract_skills("Python resume", []) == []

    def test_handles_resume_with_no_matches(self):
        assert extract_skills("No relevant skills here.", ["Python", "SQL"]) == []


class TestExtractExperience:
    def test_extracts_explicit_experience_phrase(self):
        assert extract_experience("3 years of experience") == 3
        assert extract_experience("3 years experience") == 3
        assert extract_experience("5 year experience") == 5
        assert extract_experience("2 yrs experience") == 2

    def test_returns_none_for_ambiguous_text(self):
        assert extract_experience("graduated in 2020 with a degree") is None
        assert extract_experience("project lasted 2 years") is None
        assert extract_experience("2 years ago I started studying") is None

    def test_returns_none_for_no_match(self):
        assert extract_experience("Python developer") is None

    def test_returns_none_for_non_string_input(self):
        assert extract_experience(None) is None
        assert extract_experience(123) is None

    def test_handles_blank_text(self):
        assert extract_experience("") is None
