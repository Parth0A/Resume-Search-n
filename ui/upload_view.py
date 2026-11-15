"""Card 1 — upload a CSV dataset or individual resume files."""

from __future__ import annotations

import time
from html import escape
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from resume_search.config import DATASET_EXTENSIONS, DOCUMENT_EXTENSIONS, MAX_UPLOAD_MB
from resume_search.dataset import (
    documents_to_dataframe,
    read_resume_csv,
    validate_resume_dataframe,
    validate_upload,
)
from resume_search.ranking import build_index_from_dataframe
from ui import components, state

_STEPS = ("Reading file", "Validating columns", "Building search index")


def accepted_types(include_csv: bool = True) -> list[str]:
    """File extensions the uploader accepts (without dots)."""
    extensions = (DATASET_EXTENSIONS | DOCUMENT_EXTENSIONS) if include_csv else DOCUMENT_EXTENSIONS
    return sorted(extension.lstrip(".") for extension in extensions)


def _human_size(size: int) -> str:
    if size >= 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    return f"{max(1, size // 1024)} KB"


def _read(files: list[Any]) -> tuple[pd.DataFrame, list[str]]:
    """Validate every file (type and size) before parsing, then read them."""
    csv_files = [file for file in files if Path(file.name).suffix.lower() in DATASET_EXTENSIONS]
    if csv_files and len(files) > 1:
        raise ValueError("Upload either one CSV dataset or several PDF, DOCX and TXT resumes, not both.")
    for file in files:
        validate_upload(file.name, file.size, DATASET_EXTENSIONS | DOCUMENT_EXTENSIONS)
    if csv_files:
        return read_resume_csv(csv_files[0].getvalue()), []
    return documents_to_dataframe([(file.name, file.getvalue()) for file in files])


def _prepare(files: list[Any]) -> dict[str, Any] | None:
    """Parse and index the upload once, timing each step in an st.status box."""
    timings: list[float] = []
    with st.status("Preparing your dataset…", expanded=True) as status:
        try:
            st.write(f"⏳ {_STEPS[0]}…")
            started = time.perf_counter()
            raw, warnings = _read(files)
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
            status.update(label="Could not read this upload", state="error", expanded=True)
            st.error(str(error))
            return None
        status.update(label="Dataset ready", state="complete", expanded=False)
    single = len(files) == 1
    return {
        "file_id": tuple(file.file_id for file in files),
        "name": files[0].name if single else f"{len(files)} resume files",
        "kind": Path(files[0].name).suffix.lstrip(".").upper() if single else "DOCS",
        "size": sum(file.size for file in files),
        "count": index.size,
        "index": index,
        "df": df,
        "timings": timings,
        "warnings": warnings,
    }


def _status_list(timings: list[float]) -> str:
    items = "".join(
        f'<li><span class="rs-tick">✓</span>{label}<span class="rs-time">{seconds:.2f}s</span></li>'
        for label, seconds in zip(_STEPS, timings, strict=True)
    )
    return f'<ul class="rs-status">{items}</ul>'


def _file_row(dataset: dict[str, Any]) -> str:
    kind = dataset.get("kind") or Path(dataset["name"]).suffix.lstrip(".").upper() or "FILE"
    return (
        f'<div class="rs-file"><span class="rs-file-tile">{escape(kind[:4])}</span><div>'
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
                "Resume files", type=accepted_types(), accept_multiple_files=True, label_visibility="collapsed",
                key=f"uploader_{st.session_state[state.UPLOADER_VERSION]}",
                help="One CSV with a resume-text column (Resume_str, Resume, ResumeText, Text or Content; "
                     "optional Category and Name), or several PDF, DOCX and TXT resumes.",
            )
            if uploaded:
                prepared = _prepare(list(uploaded))
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
        for warning in dataset.get("warnings", []):
            st.warning(components.md(warning))
