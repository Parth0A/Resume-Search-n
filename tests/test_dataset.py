"""Tests for resume_search.dataset."""

from __future__ import annotations

import pandas as pd
import pytest

from resume_search.dataset import (
    find_resume_column,
    is_resume_text_usable,
    load_resumes,
    read_resume_csv,
)


class TestLoadResumes:
    def test_loads_valid_csv(self):
        csv_content = "Resume_str,Category\nPython developer with 3 years of experience,Engineering\n"
        df = load_resumes(csv_content.encode("utf-8"))
        assert not df.empty
        assert "Resume_str" in df.columns

    def test_accepts_alternate_resume_column(self):
        df = load_resumes(b"Resume,Category\nBackend engineer resume\n")
        assert "Resume" in df.columns

    def test_accepts_category_column(self):
        df = load_resumes(b"Resume_str,Category\nResume text,Engineering\n")
        assert "Category" in df.columns

    def test_reads_only_needed_columns(self):
        df = read_resume_csv(b"Resume_str,Category,Name,Salary\ntext,Eng,Ann,100\n")
        assert set(df.columns) == {"Resume_str", "Category", "Name"}

    def test_reads_latin1(self):
        df = load_resumes("Resume_str\nCaf\xe9 manager resume\n".encode("latin-1"))
        assert df.iloc[0]["Resume_str"].startswith("Caf")

    def test_rejects_empty_file(self):
        with pytest.raises(ValueError):
            load_resumes(b"")

    def test_rejects_file_with_no_rows(self):
        with pytest.raises(ValueError):
            load_resumes(b"Resume_str,Category\n")

    def test_rejects_csv_without_resume_column(self):
        with pytest.raises(ValueError):
            load_resumes(b"Name,Email\nAlice,a@example.com\n")

    def test_rejects_csv_with_only_blank_resumes(self):
        with pytest.raises(ValueError):
            load_resumes(b"Resume_str,Category\n,\n,\n")

    def test_rejects_malformed_csv(self):
        with pytest.raises(ValueError):
            load_resumes(b"not a csv at all @@@@")


class TestFindResumeColumn:
    def test_finds_preferred_column(self):
        df = pd.DataFrame({"Resume_str": ["text"], "Category": ["eng"]})
        assert find_resume_column(df) == "Resume_str"

    def test_finds_alternate_column(self):
        df = pd.DataFrame({"ResumeText": ["text"], "Category": ["eng"]})
        assert find_resume_column(df) == "ResumeText"

    def test_tries_ordered_alternatives(self):
        assert find_resume_column(pd.DataFrame({"Content": ["text"]})) == "Content"

    def test_raises_when_no_column_found(self):
        with pytest.raises(ValueError):
            find_resume_column(pd.DataFrame({"Name": ["Alice"]}))


class TestIsResumeTextUsable:
    def test_returns_true_for_usable_text(self):
        assert is_resume_text_usable(pd.Series(["", "  ", "Python engineer"])) is True

    def test_returns_false_for_blank_text(self):
        assert is_resume_text_usable(pd.Series(["", "  ", "!!!", "\t"])) is False

    def test_handles_non_string_values(self):
        assert is_resume_text_usable(pd.Series([None, 123, "useful text"])) is True
