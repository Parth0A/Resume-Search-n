"""Preparing ranked results for CSV export."""

from __future__ import annotations

from typing import Any

import pandas as pd


def candidate_label(row: dict[str, Any]) -> str:
    """Return the display name of a result row (its name or "Candidate N")."""
    name = str(row.get("name") or "").strip()
    return name or f"Candidate {row['original_index'] + 1}"


def prepare_export_data(results: list[dict[str, Any]]) -> pd.DataFrame:
    """Turn ranked result rows into a tidy dataframe."""
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
            "Resume Text": row["resume_text"],
        }
        for rank, row in enumerate(results, start=1)
    ]
    return pd.DataFrame(records)


def export_csv(results: list[dict[str, Any]]) -> str:
    """Return ranked results as CSV text."""
    return prepare_export_data(results).to_csv(index=False)
