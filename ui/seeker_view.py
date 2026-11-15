"""Job-seeker page: check your own resume against a job description."""

from __future__ import annotations

import logging

import streamlit as st

from resume_search.config import DOCUMENT_EXTENSIONS, SKILL_OPTIONS
from resume_search.dataset import read_document
from resume_search.ranking import match_resume_to_job
from ui import components

logger = logging.getLogger(__name__)

MY_RESUME = "rs_my_resume"  # resume text used for the check and by AI tools
MY_RESULT = "rs_my_result"


def _result_card() -> None:
    result = st.session_state.get(MY_RESULT)
    with st.container(key="card_my_result"):
        components.render(components.card_header(
            3, "Your match", "Text similarity between your resume and the job. It is not a hiring decision."
        ))
        if result is None:
            components.render(components.empty_state(
                "No check yet", "Add your resume and a job description, then press Check my resume."
            ))
            return
        requested = len(result["matched_skills"]) + len(result["missing_skills"])
        components.render(components.kpi_tiles([
            (f"{result['score']:.2f}", "Match score"),
            (f"{len(result['matched_skills'])}/{requested}" if requested else "—", "Skills found"),
            (f"{result['experience']} yrs" if result["experience"] is not None else "Not detected", "Experience stated"),
            (f"{result['word_count']:,}", "Words in resume"),
        ]))
        components.render(components.section_label("Skills"))
        if requested:
            components.render(
                '<div class="rs-chips">'
                + "".join(components.chip(skill, "matched") for skill in result["matched_skills"])
                + "".join(components.chip(skill, "missing") for skill in result["missing_skills"])
                + "</div>"
            )
        else:
            components.render('<span class="rs-muted">Pick skills above to check them one by one.</span>')
        components.render(components.section_label("Why this score"))
        components.render(components.term_bars(result["top_terms"]))
        if result["missing_skills"]:
            components.render(components.info_strip(
                "Not found in your resume: " + ", ".join(result["missing_skills"])
                + ". If you have these skills, say so clearly, in the words the job uses."
            ))
        st.caption("Use AI tools → Skill gap analyser for a detailed, evidence-based comparison.")


def render_seeker_page() -> None:
    """Draw the job-seeker resume check (one form, one primary button)."""
    with st.form("seeker_form", border=False):
        resume_col, job_col = st.columns(2, gap="medium")
        with resume_col, st.container(key="card_my_resume"):
            components.render(components.card_header(1, "Your resume", "Upload a PDF, DOCX or TXT file, or paste the text"))
            uploaded = st.file_uploader("Resume file", type=sorted(ext.lstrip(".") for ext in DOCUMENT_EXTENSIONS))
            pasted = st.text_area("…or paste your resume text", height=160,
                                  value=st.session_state.get(MY_RESUME, ""))
        with job_col, st.container(key="card_my_job"):
            components.render(components.card_header(2, "Target job", "Paste the job description you are applying for"))
            job_description = st.text_area("Job description", height=170,
                                           placeholder="Paste the full job description here.")
            skills = st.multiselect("Skills to check (optional)", SKILL_OPTIONS, accept_new_options=True,
                                    placeholder="Pick or type skills the job asks for")
            submitted = st.form_submit_button("Check my resume", type="primary", use_container_width=True)
    if submitted:
        _check(uploaded, pasted, job_description, skills)
    _result_card()


def _check(uploaded: object, pasted: str, job_description: str, skills: list[str]) -> None:
    try:
        with st.spinner("Comparing your resume with the job…"):
            resume_text = read_document(uploaded.getvalue(), uploaded.name) if uploaded is not None else pasted
            st.session_state[MY_RESULT] = match_resume_to_job(resume_text, job_description, skills)
            st.session_state[MY_RESUME] = resume_text
    except ValueError as error:
        st.error(str(error))
    except Exception:
        logger.exception("Resume check failed")
        st.error("Something went wrong while checking your resume. Try again.")
