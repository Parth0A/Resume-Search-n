"""Card 3 — ranked results, selected-candidate panel, profiles and charts."""

from __future__ import annotations

import logging
from html import escape
from typing import Any

import pandas as pd
import streamlit as st

from resume_search.ai_features import GeminiConfigurationError, analyze_resume
from resume_search.export import candidate_label, export_csv
from resume_search.shortlists import add_to_shortlist
from resume_search.text import redact_contact_details
from ui import components, state
from ui.ai_view import gemini_api_key

logger = logging.getLogger(__name__)
_DESCRIPTION = "Scores show text similarity between the role and each resume. They are not hiring decisions."


def _years(row: dict[str, Any]) -> str:
    return f"{row['experience']} yrs" if row["experience"] is not None else "Not detected"


def _resume_text(row: dict[str, Any], blind: bool) -> str:
    return redact_contact_details(row["resume_text"]) if blind else row["resume_text"]


def render_results_card() -> None:
    """Draw the results card (or an empty state before the first search)."""
    results = st.session_state.get(state.RESULTS)
    with st.container(key="card_results"):
        components.render(components.card_header(3, "Results", _DESCRIPTION))
        if results is None:
            components.render(components.empty_state(
                "No search yet", "Upload a dataset, describe the role and press Search candidates."
            ))
            return
        rows: list[dict[str, Any]] = results["results"]
        top = rows[0]["score"] if rows else 0.0
        components.render(components.kpi_tiles([
            (f"{top:.2f}", "Top similarity score"),
            (f"{results['total_candidates']:,}", "Resumes searched"),
            (f"{results['matched_candidates']:,}", "Candidates matched"),
            (f"{results['search_seconds'] * 1000:.0f} ms", "Search time"),
        ]))
        if not rows:
            components.render(components.empty_state(
                "No matching resumes", "Try a broader title, fewer skills or a lower minimum experience."
            ))
            return
        _, export_col = st.columns([4, 1])
        with export_col:
            st.download_button(
                "Export CSV", data=export_csv(rows, blind=results["blind"]),
                file_name="resume_search_results.csv", mime="text/csv", use_container_width=True,
                on_click="ignore",
            )
        overview, profiles, charts = st.tabs(["Overview", "Profiles", "Charts"])
        with overview:
            _overview(results, rows)
        with profiles:
            _profiles(results, rows)
        with charts:
            _charts(results, rows)


def _overview(results: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    table_col, panel_col = st.columns([3, 2], gap="medium")
    with table_col:
        table = pd.DataFrame({
            "#": range(1, len(rows) + 1),
            "Candidate": [candidate_label(row) for row in rows],
            "Role": [row["category"] or "—" for row in rows],
            "Experience": [_years(row) for row in rows],
            "Matched skills": [row["matched_skills"] for row in rows],
            "Relevance": [round(row["score"], 2) for row in rows],
        })
        event = st.dataframe(
            table, hide_index=True, use_container_width=True, on_select="rerun",
            selection_mode="single-row", key="results_table",
            column_config={
                "#": st.column_config.NumberColumn(width=36),
                "Experience": st.column_config.TextColumn(width=96),
                "Matched skills": st.column_config.ListColumn(),
                "Relevance": st.column_config.ProgressColumn(min_value=0.0, max_value=1.0, format="%.2f", width=110),
            },
        )
        selected_rows = event.selection.rows if event and event.selection else []
        if selected_rows:
            st.session_state[state.SELECTED] = selected_rows[0]
        st.caption("Select a row to see the candidate's details.")
    position = min(st.session_state.get(state.SELECTED, 0), len(rows) - 1)
    with panel_col:
        _candidate_panel(results, rows[position], position)


def _candidate_panel(results: dict[str, Any], row: dict[str, Any], position: int) -> None:
    name = candidate_label(row)
    blind = results["blind"]
    with st.container(key="panel_candidate"):
        components.render(
            '<div class="rs-cand-head">'
            f"{components.avatar(name, 52)}"
            f'<div><div class="rs-cand-name">{escape(name)}</div>'
            f'<div class="rs-cand-meta">{escape(row["category"] or "Role not specified")} · {escape(_years(row))}</div></div>'
            f"{components.score_ring(row['score'])}</div>"
        )
        components.render(components.section_label("Skills"))
        if results["skills_requested"]:
            components.render(
                '<div class="rs-chips">'
                + "".join(components.chip(skill, "matched") for skill in row["matched_skills"])
                + "".join(components.chip(skill, "missing") for skill in row["missing_skills"])
                + "</div>"
            )
        else:
            components.render('<span class="rs-muted">No skills were requested.</span>')
        components.render(components.section_label("Why this score"))
        components.render(components.term_bars(row.get("top_terms", [])))
        if blind:
            components.render(components.info_strip("Contact details hidden — blind screening is on."))
        shortlist_col, ai_col, view_col = st.columns(3)
        with shortlist_col:
            shortlist = st.button("Shortlist", key=f"shortlist_{position}", type="primary",
                                  use_container_width=True, disabled=not state.is_recruiter(),
                                  help=None if state.is_recruiter() else "Shortlists are for recruiter accounts.")
        with ai_col:
            summarise = st.button("AI summary", key=f"ai_summary_{position}", use_container_width=True)
        with view_col:
            view_key = f"view_resume_{row['original_index']}"
            if st.button("View resume", key=f"view_{position}", use_container_width=True):
                st.session_state[view_key] = not st.session_state.get(view_key, False)
        if shortlist:
            _shortlist(results, row, name)
        if summarise:
            _summarise(row, blind)
        summary = st.session_state[state.AI_OUTPUTS].get(f"summary_{row['original_index']}")
        if summary:
            st.markdown("**AI summary**")
            st.write(summary)
            st.caption("AI output can be wrong. Verify it against the resume.")
        if st.session_state.get(view_key):
            st.text_area("Resume text", _resume_text(row, blind), height=220, disabled=True,
                         key=f"resume_text_{row['original_index']}")


def _shortlist(results: dict[str, Any], row: dict[str, Any], name: str) -> None:
    user = state.current_user()
    title = results.get("job_title") or "My shortlist"
    try:
        added = add_to_shortlist(user["id"], title, {
            "candidate": name, "score": row["score"], "matched_skills": row["matched_skills"],
            "dataset": results.get("dataset_name", ""), "original_index": row["original_index"],
        })
    except Exception:
        logger.exception("Could not save shortlist item")
        st.error("Could not save to the shortlist. Try again.")
        return
    if added:
        st.success(f"Added to shortlist “{title}”.")
    else:
        st.info(f"Already in shortlist “{title}”.")


def _summarise(row: dict[str, Any], blind: bool) -> None:
    try:
        with st.spinner("Asking Gemini for a summary…"):
            profile = analyze_resume(_resume_text(row, blind), api_key=gemini_api_key())
    except (GeminiConfigurationError, ValueError, RuntimeError) as error:
        st.error(str(error))
        return
    except Exception:
        logger.exception("Gemini summary failed")
        st.error("Gemini request failed. Check your API key, connection and free-tier quota.")
        return
    st.session_state[state.AI_OUTPUTS][f"summary_{row['original_index']}"] = profile.get("summary", "")


def _profiles(results: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    for rank, row in enumerate(rows, start=1):
        with st.expander(f"#{rank} · {candidate_label(row)} · {row['score']:.2f}"):
            components.render(components.relevance_bar(row["score"]))
            st.markdown(f"**Role:** {row['category'] or 'Not specified'}  \n**Experience:** {_years(row)}")
            if results["skills_requested"]:
                components.render(components.chips(row["matched_skills"], "matched", "No requested skills found."))
                components.render(components.chips(row["missing_skills"], "missing", "No missing skills."))
            st.text_area("Resume text", _resume_text(row, results["blind"]), height=160, disabled=True,
                         key=f"profile_text_{row['original_index']}", label_visibility="collapsed")


def _charts(results: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    scores = pd.DataFrame({"Candidate": [candidate_label(row) for row in rows],
                           "Relevance": [row["score"] for row in rows]})
    st.markdown("**Relevance by candidate**")
    st.bar_chart(scores, x="Candidate", y="Relevance", color="#4F46E5", horizontal=True)
    if results["skills_requested"]:
        coverage = pd.DataFrame({
            "Skill": results["skills_requested"],
            "Candidates with skill": [sum(skill in row["matched_skills"] for row in rows)
                                      for skill in results["skills_requested"]],
        })
        st.markdown("**Skill coverage in this shortlist**")
        st.bar_chart(coverage, x="Skill", y="Candidates with skill", color="#10B981")
