"""AI tools page (optional Google Gemini features)."""

from __future__ import annotations

import json
import logging
import os
from collections.abc import Callable
from typing import Any

import streamlit as st

from resume_search.ai_features import (
    GeminiConfigurationError,
    analyze_resume,
    analyze_skill_gap,
    generate_job_description,
)
from resume_search.export import candidate_label
from resume_search.text import redact_contact_details
from ui import components, state

logger = logging.getLogger(__name__)

_NOTICE = (
    "Only the one resume you select (with contact details hidden) and your prompt text are sent to "
    "Google Gemini, and only when you press a button."
)


_NO_RESUME_HINT = (
    "Recruiters: upload a dataset on Screen candidates. Job seekers: add your resume on Check my resume."
)


def gemini_api_key() -> str | None:
    """Read the Gemini key from Streamlit secrets or the environment (never from user input)."""
    try:
        secret = st.secrets.get("GEMINI_API_KEY")
    except Exception:  # no secrets.toml configured
        secret = None
    return (secret or os.getenv("GEMINI_API_KEY") or "").strip() or None


def _run(key: str, label: str, action: Callable[[], dict[str, Any]]) -> None:
    try:
        with st.spinner(label):
            st.session_state[state.AI_OUTPUTS][key] = action()
    except (GeminiConfigurationError, ValueError, RuntimeError) as error:
        st.error(str(error))
    except Exception:
        logger.exception("Gemini request failed")
        st.error("Gemini request failed. Check your API key, connection and free-tier quota.")


def _resume_choices() -> tuple[list[str], list[str]]:
    """Labels and (redacted) texts of the resumes the user can analyse."""
    if not state.is_recruiter():
        own = str(st.session_state.get("rs_my_resume") or "")
        return (["My resume"], [redact_contact_details(own)]) if own.strip() else ([], [])
    dataset = st.session_state.get(state.DATASET)
    if dataset is None:
        return [], []
    index = dataset["index"]
    labels = [
        candidate_label({"name": index.names[position], "original_index": position})
        for position in range(index.size)
    ]
    return labels, [redact_contact_details(text) for text in index.texts]


def render_ai_page() -> None:
    """Draw the three Gemini tools."""
    outputs: dict[str, Any] = st.session_state[state.AI_OUTPUTS]
    with st.container(key="card_ai"):
        components.render(components.card_header("AI", "Gemini AI tools", _NOTICE))
        if gemini_api_key() is None:
            st.warning("Gemini is not configured. Add GEMINI_API_KEY to a local .env file or to Streamlit secrets.")
        labels, texts = _resume_choices()
        profile_tab, gap_tab, jd_tab = st.tabs(["Resume intelligence", "Skill gap analyser", "Job description generator"])
        with profile_tab:
            if not labels:
                st.info(_NO_RESUME_HINT)
            else:
                choice = st.selectbox("Resume", range(len(labels)), format_func=labels.__getitem__, key="ai_profile_pick")
                if st.button("Analyse selected resume", key="ai_profile_run", type="primary"):
                    _run("profile", "Analysing one resume…",
                         lambda: analyze_resume(texts[choice], api_key=gemini_api_key()))
                if "profile" in outputs:
                    st.json(outputs["profile"])
        with gap_tab:
            if not labels:
                st.info(_NO_RESUME_HINT)
            else:
                choice = st.selectbox("Resume", range(len(labels)), format_func=labels.__getitem__, key="ai_gap_pick")
                description = st.text_area("Target job description", height=170, key="ai_gap_description")
                if st.button("Analyse skill gaps", key="ai_gap_run", type="primary"):
                    _run("gap", "Comparing the resume with the job…",
                         lambda: analyze_skill_gap(texts[choice], description, api_key=gemini_api_key()))
                if "gap" in outputs:
                    st.json(outputs["gap"])
        with jd_tab:
            _job_description_tool(outputs)
        st.caption("AI output can be wrong. Verify details and never use it as the only basis for a hiring decision.")


def _job_description_tool(outputs: dict[str, Any]) -> None:
    with st.form("jd_form", border=False):
        title = st.text_input("Job title", placeholder="e.g. Junior Python Developer")
        skills = st.text_input("Required skills (comma-separated)", placeholder="Python, SQL, Git")
        level_col, type_col = st.columns(2)
        with level_col:
            level = st.selectbox("Experience level", ["Entry level", "Junior", "Mid-level", "Senior", "Internship"])
        with type_col:
            kind = st.selectbox("Employment type", ["Full-time", "Part-time", "Internship", "Contract", "Temporary"])
        context = st.text_area("Additional context (optional)", height=90)
        submitted = st.form_submit_button("Generate job description", type="primary")
    if submitted:
        skill_list = [item.strip() for item in skills.split(",") if item.strip()]
        _run("job_description", "Drafting a job description…",
             lambda: generate_job_description(title, skill_list, level, kind, context, api_key=gemini_api_key()))
    if "job_description" in outputs:
        st.json(outputs["job_description"])
        st.download_button(
            "Download job description (JSON)",
            data=json.dumps(outputs["job_description"], indent=2, ensure_ascii=False),
            file_name="generated_job_description.json", mime="application/json", on_click="ignore",
        )
