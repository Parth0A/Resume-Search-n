"""Tests for resume_search.ranking."""

from __future__ import annotations

import pandas as pd
import pytest

from resume_search.ranking import (
    build_index,
    build_search_query,
    explain_score,
    rank,
    search_index,
    search_resumes,
    validate_job_title,
)


def _rank(resumes, query, *, experience=None, min_experience=None, limit=5, skills=None):
    index = build_index(resumes, ["Eng"] * len(resumes))
    if experience is not None:
        index.experience = list(experience)
    return rank(index, query, skills or [], min_experience, limit)


class TestValidateJobTitle:
    def test_accepts_valid_job_title(self):
        assert validate_job_title("Software Engineer") == "software engineer"

    @pytest.mark.parametrize("title", ["", "   ", "!!!"])
    def test_rejects_unusable_titles(self, title):
        with pytest.raises(ValueError):
            validate_job_title(title)


class TestBuildSearchQuery:
    def test_combines_job_title_and_skills(self):
        query = build_search_query("Software Engineer", ["Python", "SQL"])
        assert "software engineer" in query
        assert "python" in query
        assert "sql" in query

    def test_validates_job_title(self):
        with pytest.raises(ValueError):
            build_search_query("", ["Python"])

    def test_handles_empty_skills(self):
        assert build_search_query("Engineer", []) == "engineer"


class TestRank:
    def test_ranks_by_descending_score(self):
        result = _rank(["Python developer with deep experience", "Java developer"], "python developer", limit=2)
        assert len(result) == 2
        assert result[0]["score"] >= result[1]["score"]

    def test_respects_result_limit(self):
        assert len(_rank(["Python developer"] * 12, "python developer", limit=5)) == 5

    def test_returns_empty_for_no_usable_text(self):
        assert _rank(["!!!", "   "], "python") == []

    def test_tie_breaks_by_original_position(self):
        result = _rank(["Python developer", "Python developer"], "python developer")
        assert result[0]["original_index"] < result[1]["original_index"]

    def test_deterministic_order_for_ties(self):
        first = _rank(["Python developer", "Python developer"], "python developer", limit=2)
        second = _rank(["Python developer", "Python developer"], "python developer", limit=2)
        assert [r["original_index"] for r in first] == [r["original_index"] for r in second]


class TestExperienceFiltering:
    def test_filters_by_minimum_experience(self):
        result = _rank(
            ["Engineer with 2 years of experience", "Engineer with 8 years of experience"],
            "engineer", experience=[2, 8], min_experience=5,
        )
        assert [r["original_index"] for r in result] == [1]

    def test_excludes_unknown_experience(self):
        result = _rank(
            ["Engineer resume", "Engineer with 4 years experience"],
            "engineer", experience=[None, 4], min_experience=3,
        )
        assert [r["original_index"] for r in result] == [1]

    def test_includes_all_when_no_minimum(self):
        result = _rank(["Engineer with 2 years of experience", "Engineer resume"], "engineer", experience=[2, None])
        assert len(result) == 2


class TestSearchResumes:
    def test_returns_ranked_results(self):
        df = pd.DataFrame({
            "Resume_str": ["Python developer with 3 years experience", "Java developer"],
            "Category": ["Engineering", "Engineering"],
        })
        results = search_resumes(df=df, job_title="Python developer", skills=[], min_experience=None, limit=10)
        assert results["total_candidates"] == 2
        assert len(results["results"]) == 2
        assert results["results"][0]["score"] >= results["results"][1]["score"]
        assert results["search_seconds"] >= 0

    def test_reports_matching_and_missing_skills(self):
        df = pd.DataFrame({"Resume_str": ["Python and SQL developer"], "Category": ["Engineering"]})
        row = search_resumes(df=df, job_title="developer", skills=["Python", "SQL", "Java"],
                             min_experience=None, limit=10)["results"][0]
        assert "Python" in row["matched_skills"]
        assert "SQL" in row["matched_skills"]
        assert "Java" in row["missing_skills"]

    def test_applies_minimum_experience_filter(self):
        df = pd.DataFrame({
            "Resume_str": ["Engineer with 2 years of experience", "Engineer with 6 years experience"],
            "Category": ["Eng", "Eng"],
        })
        results = search_resumes(df=df, job_title="engineer", skills=[], min_experience=5, limit=10)
        assert len(results["results"]) == 1
        assert results["results"][0]["experience"] == 6

    def test_excludes_unknown_experience_with_minimum(self):
        df = pd.DataFrame({
            "Resume_str": ["Engineer resume", "Engineer with 3 years experience"],
            "Category": ["Eng", "Eng"],
        })
        results = search_resumes(df=df, job_title="engineer", skills=[], min_experience=3, limit=10)
        indices = [row["original_index"] for row in results["results"]]
        assert 0 not in indices
        assert 1 in indices

    def test_respects_result_limit(self):
        df = pd.DataFrame({"Resume_str": ["Python developer"] * 15, "Category": ["Eng"] * 15})
        results = search_resumes(df=df, job_title="python developer", skills=[], min_experience=None, limit=5)
        assert len(results["results"]) == 5

    def test_handles_duplicate_skills(self):
        df = pd.DataFrame({"Resume_str": ["Python developer"], "Category": ["Eng"]})
        row = search_resumes(df=df, job_title="developer", skills=["Python", "Python", "SQL"],
                             min_experience=None, limit=10)["results"][0]
        assert row["matched_skills"] == ["Python"]
        assert row["missing_skills"] == ["SQL"]

    def test_handles_no_keyword_overlap_safely(self):
        df = pd.DataFrame({"Resume_str": ["Java developer", "C++ developer"], "Category": ["Eng", "Eng"]})
        results = search_resumes(df=df, job_title="rust developer", skills=[], min_experience=None, limit=10)
        assert isinstance(results, dict)
        assert "results" in results

    def test_rejects_punctuation_only_job_title(self):
        df = pd.DataFrame({"Resume_str": ["Python developer"], "Category": ["Eng"]})
        with pytest.raises(ValueError):
            search_resumes(df=df, job_title="!!!", skills=[], min_experience=None, limit=10)

    def test_raises_for_blank_job_title(self):
        df = pd.DataFrame({"Resume_str": ["Python developer"], "Category": ["Eng"]})
        with pytest.raises(ValueError):
            search_resumes(df=df, job_title="", skills=[], min_experience=None, limit=5)

    def test_raises_for_invalid_limit(self):
        df = pd.DataFrame({"Resume_str": ["Python developer"], "Category": ["Eng"]})
        with pytest.raises(ValueError):
            search_resumes(df=df, job_title="developer", skills=[], min_experience=None, limit=0)

    def test_skills_requested_is_preserved(self):
        df = pd.DataFrame({"Resume_str": ["Python developer"], "Category": ["Eng"]})
        results = search_resumes(df=df, job_title="developer", skills=["Python"], min_experience=None, limit=10)
        assert results["skills_requested"] == ["Python"]


class TestMixedCaseRegression:
    def test_capitalized_resume_ranks_first(self):
        df = pd.DataFrame({
            "Resume_str": [
                "Accountant handling Payroll and Tax returns.",
                "PYTHON DEVELOPER skilled in Django, SQL and REST APIs.",
                "Graphic Designer using Photoshop and Illustrator.",
            ],
            "Category": ["Finance", "Engineering", "Design"],
        })
        results = search_resumes(df=df, job_title="Python Developer", skills=["Django"],
                                 min_experience=None, limit=3)
        top = results["results"][0]
        assert top["original_index"] == 1
        assert top["score"] > 0.3


class TestSearchOptions:
    def test_job_description_alone_is_enough(self):
        index = build_index(["Chef cooking Italian pasta", "Python developer building APIs"])
        results = search_index(index, "", [], None, 5, job_description="We need a Python API developer.")
        assert results["results"][0]["original_index"] == 1

    def test_job_description_extends_title(self):
        query = build_search_query("Engineer", ["SQL"], "Build Kafka pipelines")
        assert query.startswith("engineer sql")
        assert "kafka" in query

    def test_include_unknown_experience(self):
        index = build_index(["Engineer resume", "Engineer with 4 years experience", "Engineer with 1 years experience"])
        strict = search_index(index, "engineer", [], 3, 5)
        relaxed = search_index(index, "engineer", [], 3, 5, include_unknown_experience=True)
        assert [r["original_index"] for r in strict["results"]] == [1]
        assert sorted(r["original_index"] for r in relaxed["results"]) == [0, 1]

    def test_matched_candidates_counts_positive_scores(self):
        index = build_index(["Python developer", "Chef", "Python tester"])
        assert search_index(index, "python", [], None, 1)["matched_candidates"] == 2


class TestExplainScore:
    def test_contributions_sum_to_score(self):
        index = build_index(["Python developer with Django and SQL", "Chef"])
        result = search_index(index, "Python developer", ["SQL"], None, 1)["results"][0]
        terms = dict(result["top_terms"])
        assert set(terms) <= {"python", "developer", "sql"}
        assert abs(sum(terms.values()) - result["score"]) < 1e-9

    def test_no_index(self):
        assert explain_score(build_index(["!!!"]), "python", 0) == []


def test_search_index_reuses_prepared_index():
    index = build_index(["Python developer", "Chef"], ["Eng", "Food"], ["Ann", "Bo"])
    first = search_index(index, "python", [], None, 5)
    second = search_index(index, "chef", [], None, 5)
    assert first["results"][0]["name"] == "Ann"
    assert second["results"][0]["name"] == "Bo"
