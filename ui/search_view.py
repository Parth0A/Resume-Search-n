"""Card 2 — describe the role and run a search."""

from __future__ import annotations

import logging
from typing import Any

import streamlit as st

from resume_search.config import (
    DEFAULT_RESULTS_LIMIT,
    EXPERIENCE_OPTIONS,
    JOB_ROLES,
    RESULT_LIMIT_OPTIONS,
    SKILL_OPTIONS,
)
from resume_search.hybrid import is_available as hybrid_available
from resume_search.ranking import search_index
from ui import components, state

logger = logging.getLogger(__name__)
_METHODS = {"TF-IDF (fast)": "tfidf", "Hybrid (semantic)": "hybrid"}


def _years(option: str) -> int | None:
    return None if option == EXPERIENCE_OPTIONS[0] else int(option.split()[0])


def render_search_card() -> None:
    """Draw the search form; results go to session state."""
    dataset = st.session_state.get(state.DATASET)
    with st.container(key="card_search"):
        components.render(components.card_header(
            2, "Describe the role", "Job title and skills, or paste a full job description"
        ))
        with st.form("search_form", clear_on_submit=False, border=False):
            title_col, exp_col, limit_col = st.columns([5, 3, 2])
            with title_col:
                job_title = st.selectbox(
                    "Job title", JOB_ROLES, index=None, accept_new_options=True,
                    placeholder="Choose or type a role",
                )
            with exp_col:
                experience = st.selectbox("Minimum experience", EXPERIENCE_OPTIONS)
            with limit_col:
                limit = st.selectbox(
                    "Show", RESULT_LIMIT_OPTIONS, index=RESULT_LIMIT_OPTIONS.index(DEFAULT_RESULTS_LIMIT)
                )
            skills = st.multiselect(
                "Required skills", SKILL_OPTIONS, accept_new_options=True,
                placeholder="Pick skills or type your own and press Enter",
            )
            with st.expander("Paste job description (optional)"):
                job_description = st.text_area(
                    "Job description", height=150, label_visibility="collapsed",
                    placeholder="Paste the full job description to rank against it.",
                )
            method_label = st.radio(
                "Ranking method", list(_METHODS), horizontal=True,
                help="Hybrid mixes TF-IDF with sentence embeddings (all-MiniLM-L6-v2). "
                     "It needs the optional sentence-transformers package and is slower the first time.",
            )
            blind_col, unknown_col, button_col = st.columns([1.25, 1.75, 1.45], vertical_alignment="center")
            with blind_col:
                blind = st.toggle("Blind screening", value=True)
            with unknown_col:
                include_unknown = st.toggle("Include unknown experience", value=True)
            with button_col:
                submitted = st.form_submit_button(
                    "Search candidates", type="primary", use_container_width=True, disabled=dataset is None
                )
        st.caption(
            "Blind screening hides e-mail addresses and phone numbers. Unknown experience keeps candidates "
            "whose experience could not be detected when a minimum is set."
            + ("" if dataset is not None else " Upload a dataset to enable search.")
        )
    if submitted and dataset is not None:
        method = _METHODS[method_label]
        if method == "hybrid" and not hybrid_available():
            st.error("Hybrid ranking needs the optional package: pip install sentence-transformers")
            return
        _run_search(dataset, job_title or "", skills, job_description, _years(experience), int(limit),
                    blind, include_unknown, method)


def _run_search(
    dataset: dict[str, Any],
    job_title: str,
    skills: list[str],
    job_description: str,
    min_years: int | None,
    limit: int,
    blind: bool,
    include_unknown: bool,
    method: str = "tfidf",
) -> None:
    try:
        with st.spinner("Ranking candidates…" if method == "tfidf" else "Ranking with embeddings (first run loads the model)…"):
            results = search_index(
                dataset["index"], job_title, skills, min_years, limit,
                job_description=job_description, include_unknown_experience=include_unknown, method=method,
            )
    except ValueError as error:
        st.error(str(error))
        return
    except Exception:
        logger.exception("Search failed")
        st.error("Something went wrong while searching. Check the dataset and try again.")
        return
    results.update({"job_title": job_title.strip(), "blind": blind, "dataset_name": dataset["name"]})
    st.session_state[state.RESULTS] = results
    st.session_state[state.SELECTED] = 0
