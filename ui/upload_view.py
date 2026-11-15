"""Card 1 — upload a resume dataset."""

from __future__ import annotations

import time
from html import escape
from pathlib import Path
from typing import Any

import streamlit as st

from resume_search.config import DATASET_EXTENSIONS, MAX_UPLOAD_MB
from resume_search.dataset import read_resume_csv, validate_resume_dataframe
from resume_search.ranking import build_index_from_dataframe
from ui import components, state

_STEPS = ("Reading file", "Validating columns", "Building search index")


def _accepted_types() -> list[str]:
    return sorted(extension.lstrip(".") for extension in DATASET_EXTENSIONS)


def _human_size(size: int) -> str:
    if size >= 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    return f"{max(1, size // 1024)} KB"


def _prepare(uploaded: Any) -> dict[str, Any] | None:
    """Parse and index the file once, timing each step in an st.status box."""
    timings: list[float] = []
    with st.status("Preparing your dataset…", expanded=True) as status:
        try:
            st.write(f"⏳ {_STEPS[0]}…")
            started = time.perf_counter()
            raw = read_resume_csv(uploaded.getvalue())
            timings.append(time.perf_counter() - started)
            st.write(f"✅ {_STEPS[0]} · {timings[-1]:.2f}s — ⏳ {_STEPS[1]}…")
            started = time.perf_counter()
            df = validate_resume_dataframe(raw)
            timings.append(time.perf_counter() - started)
            st.write(f"✅ {_STEPS[1]} · {timings[-1]:.2f}s — ⏳ {_STEPS[2]}…")
            started = time.perf_counter()
            index = build_index_from_dataframe(df)
            timings.append(time.perf_counter() - started)
        except ValueError as error:
            status.update(label="Could not read this file", state="error", expanded=True)
            st.error(str(error))
            return None
        status.update(label="Dataset ready", state="complete", expanded=False)
    return {
        "file_id": uploaded.file_id,
        "name": uploaded.name,
        "size": uploaded.size,
        "count": index.size,
        "index": index,
        "df": df,
        "timings": timings,
    }


def _status_list(timings: list[float]) -> str:
    items = "".join(
        f'<li><span class="rs-tick">✓</span>{label}<span class="rs-time">{seconds:.2f}s</span></li>'
        for label, seconds in zip(_STEPS, timings, strict=True)
    )
    return f'<ul class="rs-status">{items}</ul>'


def _file_row(dataset: dict[str, Any]) -> str:
    extension = Path(dataset["name"]).suffix.lstrip(".").upper() or "FILE"
    return (
        f'<div class="rs-file"><span class="rs-file-tile">{escape(extension[:4])}</span><div>'
        f'<div class="rs-file-name">{escape(dataset["name"])}</div>'
        f'<div class="rs-file-meta">{_human_size(dataset["size"])} · {dataset["count"]:,} resumes · ready</div>'
        "</div></div>"
    )


def render_upload_card() -> None:
    """Draw the upload card and keep the parsed dataset in session state."""
    with st.container(key="card_upload"):
        components.render(components.card_header(
            1, "Upload resumes", f"CSV dataset, or individual PDF, DOCX and TXT files · up to {MAX_UPLOAD_MB} MB"
        ))
        dataset = st.session_state.get(state.DATASET)
        if dataset is None:
            uploaded = st.file_uploader(
                "Resume file", type=_accepted_types(), label_visibility="collapsed",
                key=f"uploader_{st.session_state[state.UPLOADER_VERSION]}",
                help="CSV with a resume-text column (Resume_str, Resume, ResumeText, Text or Content). "
                     "Optional columns: Category, Name.",
            )
            if uploaded is not None:
                prepared = _prepare(uploaded)
                if prepared is not None:
                    st.session_state[state.DATASET] = prepared
                    st.session_state.pop(state.RESULTS, None)
                    st.rerun()
            return
        left, right = st.columns([3, 1], vertical_alignment="center")
        with left:
            components.render(_file_row(dataset))
        with right:
            if st.button("Replace file", key="replace_file", use_container_width=True):
                state.clear_working_data()
                st.rerun()
        components.render(_status_list(dataset["timings"]))
