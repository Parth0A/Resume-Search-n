"""Tests for resume_search.text."""

from __future__ import annotations

from resume_search.text import has_words, normalize_text, redact_contact_details, word_count


class TestNormalizeText:
    def test_normalizes_case_and_whitespace(self):
        assert normalize_text("  Python   Developer  ") == "python developer"

    def test_normalizes_punctuation_only_text(self):
        assert normalize_text("!!!") == "!!!"

    def test_handles_non_string_input(self):
        assert normalize_text(None) == ""
        assert normalize_text(123) == ""
        assert normalize_text([]) == ""

    def test_handles_empty_string(self):
        assert normalize_text("") == ""


class TestHelpers:
    def test_has_words(self):
        assert has_words("Python engineer")
        assert not has_words("!!! ...")
        assert not has_words(None)

    def test_word_count(self):
        assert word_count("one  two\nthree") == 3
        assert word_count("") == 0


class TestRedactContactDetails:
    def test_hides_email_and_phone(self):
        text = "Contact jane.doe@example.com or +1 (555) 123-4567 today."
        redacted = redact_contact_details(text)
        assert "jane.doe@example.com" not in redacted
        assert "555" not in redacted
        assert "[email hidden]" in redacted
        assert "[phone hidden]" in redacted

    def test_keeps_years_and_short_numbers(self):
        text = "Worked 2015 - 2020 with 5 years of experience."
        assert redact_contact_details(text) == text

    def test_sample_dataset_has_no_contact_details_after_redaction(self):
        import csv
        import re
        from pathlib import Path

        sample = Path(__file__).resolve().parent.parent / "data" / "sample_resumes.csv"
        with sample.open(encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        assert rows
        for row in rows:
            redacted = redact_contact_details(row["Resume_str"])
            assert "@" not in redacted
            assert not re.search(r"\+1 555", redacted)
            assert "[email hidden]" in redacted and "[phone hidden]" in redacted

    def test_non_string(self):
        assert redact_contact_details(None) == ""  # type: ignore[arg-type]
