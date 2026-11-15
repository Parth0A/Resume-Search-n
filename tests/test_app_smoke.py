"""Smoke tests: the Streamlit app starts and the main flows render without errors."""

from __future__ import annotations

from pathlib import Path

import pytest

AppTest = pytest.importorskip("streamlit.testing.v1").AppTest
APP = str(Path(__file__).resolve().parent.parent / "app.py")
SAMPLE = Path(__file__).resolve().parent.parent / "data" / "sample_resumes.csv"


def test_login_page_renders(temp_db):
    app = AppTest.from_file(APP, default_timeout=60).run()
    assert not app.exception
    assert any("Welcome back" in block.value for block in app.markdown)
    assert [field.label for field in app.text_input] == ["Email address", "Password"]


def test_signed_in_pages_render(temp_db):
    from resume_search.auth import authenticate_user, register_user
    from resume_search.dataset import load_resumes
    from resume_search.ranking import build_index_from_dataframe, search_index

    register_user("smoke@example.com", "Smoke-Test-Pass-1", "Recruiter", "Smoke Test")
    user = authenticate_user("smoke@example.com", "Smoke-Test-Pass-1")
    df = load_resumes(SAMPLE.read_bytes())
    index = build_index_from_dataframe(df)
    results = search_index(index, "Python Developer", ["Python", "Django"], None, 10)
    results.update({"job_title": "Python Developer", "blind": True, "dataset_name": "sample_resumes.csv"})

    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["rs_user"] = user
    app.session_state["rs_dataset"] = {
        "file_id": "x", "name": "sample_resumes.csv", "size": 1000, "count": index.size,
        "index": index, "df": df, "timings": [0.01, 0.0, 0.02],
    }
    app.session_state["rs_results"] = results
    app.run()
    assert not app.exception
    for page in ("shortlists", "ai", "profile", "privacy", "screen"):
        app.session_state["rs_page"] = page
        app.run()
        assert not app.exception, page


def test_job_seeker_flow(temp_db):
    from resume_search.auth import authenticate_user, register_user

    register_user("seeker@example.com", "Seeker-Test-Pass-1", "Job seeker", "Sam Seeker")
    user = authenticate_user("seeker@example.com", "Seeker-Test-Pass-1")
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["rs_user"] = user
    app.session_state["rs_page"] = "shortlists"  # recruiter-only page: must redirect
    app.run()
    assert not app.exception
    assert app.session_state["rs_page"] == "check"
    resume_box, job_box = app.text_area[0], app.text_area[1]
    resume_box.set_value("Python developer with 4 years of experience in Django, SQL and Docker.")
    job_box.set_value("We are hiring a Python Django developer who knows Docker.")
    next(button for button in app.button if button.label == "Check my resume").click()
    app.run()
    assert not app.exception
    result = app.session_state["rs_my_result"]
    assert result["score"] > 0 and result["experience"] == 4
    for page in ("ai", "profile", "privacy"):
        app.session_state["rs_page"] = page
        app.run()
        assert not app.exception, page
