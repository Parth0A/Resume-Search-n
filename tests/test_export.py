"""Tests for resume_search.export."""

from __future__ import annotations

from resume_search.export import candidate_label, export_csv, prepare_export_data


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


def test_export_csv_has_header_and_row():
    lines = export_csv([_row()]).strip().splitlines()
    assert lines[0].startswith("Rank,Candidate")
    assert len(lines) == 2
