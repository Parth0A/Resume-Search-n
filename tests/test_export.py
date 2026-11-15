"""Tests for resume_search.export."""

from __future__ import annotations

import pandas as pd
import pytest

from resume_search.export import (
    candidate_label,
    export_csv,
    prepare_export_data,
    protect_formula,
    to_safe_csv,
)


def _row(**overrides):
    row = {
        "original_index": 3,
        "name": "",
        "resume_text": "Python developer",
        "category": "Engineering",
        "score": 0.8,
        "experience": 3,
        "matched_skills": ["Python"],
        "missing_skills": ["SQL"],
    }
    row.update(overrides)
    return row


class TestPrepareExportData:
    def test_prepares_dataframe_with_expected_columns(self):
        df = prepare_export_data([_row()])
        assert not df.empty
        for column in ("Candidate", "Match Score", "Original Index"):
            assert column in df.columns
        assert df.iloc[0]["Candidate"] == "Candidate 4"
        assert df.iloc[0]["Original Index"] == 3

    def test_handles_experience_not_detected(self):
        df = prepare_export_data([_row(category=None, experience=None, matched_skills=[], missing_skills=[])])
        assert df.iloc[0]["Detected Experience"] == "Not detected"
        assert df.iloc[0]["Category"] == "Not specified"

    def test_returns_empty_dataframe_for_no_results(self):
        assert prepare_export_data([]).empty


def test_candidate_label_prefers_name():
    assert candidate_label(_row(name="Asha Rao")) == "Asha Rao"
    assert candidate_label(_row()) == "Candidate 4"


class TestFormulaInjection:
    @pytest.mark.parametrize("value", ["=1+1", "+cmd", "-2+3", "@SUM(A1)", "\t=x", "\r=x"])
    def test_dangerous_cells_are_quoted(self, value):
        assert protect_formula(value) == "'" + value

    @pytest.mark.parametrize("value", ["Python", "", "a=b", 5, None, -3.2])
    def test_safe_values_unchanged(self, value):
        assert protect_formula(value) == value

    def test_export_csv_is_protected(self):
        csv_text = export_csv([_row(name="=HYPERLINK(\"http://x\")", category="+danger",
                                    resume_text="@evil text")])
        assert "'=HYPERLINK" in csv_text
        assert "'+danger" in csv_text
        assert "'@evil text" in csv_text

    def test_to_safe_csv_protects_headers(self):
        assert to_safe_csv(pd.DataFrame({"=bad": ["ok"]})).splitlines()[0] == "'=bad"


def test_blind_export_hides_contact_details():
    csv_text = export_csv([_row(resume_text="Mail me at a.b@example.com or +44 20 7946 0958")], blind=True)
    assert "a.b@example.com" not in csv_text
    assert "7946" not in csv_text


def test_export_csv_has_header_and_row():
    lines = export_csv([_row()]).strip().splitlines()
    assert lines[0].startswith("Rank,Candidate")
    assert len(lines) == 2
