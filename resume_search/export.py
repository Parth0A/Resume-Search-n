"""Preparing ranked results for CSV export.

Every CSV produced here is protected against spreadsheet formula injection:
cells that start with ``=``, ``+``, ``-``, ``@`` (or a tab / carriage return)
are prefixed with a single quote so spreadsheet apps show them as text.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from resume_search.text import redact_contact_details

_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def protect_formula(value: Any) -> Any:
    """Prefix a string cell with ``'`` when a spreadsheet could run it as a formula."""
    if isinstance(value, str) and value.startswith(_FORMULA_PREFIXES):
        return "'" + value
    return value


def to_safe_csv(df: pd.DataFrame) -> str:
    """Return ``df`` as CSV text with every string cell formula-protected."""
    safe = df.copy()
    for column in safe.columns:
        if safe[column].dtype == object or pd.api.types.is_string_dtype(safe[column]):
            safe[column] = safe[column].map(protect_formula)
    safe.columns = [protect_formula(str(column)) for column in safe.columns]
    return safe.to_csv(index=False)


def candidate_label(row: dict[str, Any]) -> str:
    """Return the display name of a result row (its name or "Candidate N")."""
    name = str(row.get("name") or "").strip()
    return name or f"Candidate {row['original_index'] + 1}"


def prepare_export_data(results: list[dict[str, Any]], blind: bool = False) -> pd.DataFrame:
    """Turn ranked result rows into a tidy dataframe.

    With ``blind`` set, e-mail addresses and phone numbers in the resume text
    are hidden.
    """
    if not results:
        return pd.DataFrame()
    records = [
        {
            "Rank": rank,
            "Candidate": candidate_label(row),
            "Original Index": row["original_index"],
            "Category": row["category"] or "Not specified",
            "Match Score": round(row["score"], 4),
            "Detected Experience": row["experience"] if row["experience"] is not None else "Not detected",
            "Matching Skills": ", ".join(row["matched_skills"]) or "None",
            "Missing Skills": ", ".join(row["missing_skills"]) or "None",
            "Resume Text": redact_contact_details(row["resume_text"]) if blind else row["resume_text"],
        }
        for rank, row in enumerate(results, start=1)
    ]
    return pd.DataFrame(records)


def export_csv(results: list[dict[str, Any]], blind: bool = False) -> str:
    """Return ranked results as formula-safe CSV text."""
    return to_safe_csv(prepare_export_data(results, blind))
