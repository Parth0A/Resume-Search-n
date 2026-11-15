"""TF-IDF ranking of resumes against a role.

The index is built once per dataset (:func:`build_index`); every search then
only transforms the query (:func:`rank`), which keeps searches fast.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from resume_search.config import CATEGORY_COLUMN, NAME_COLUMN
from resume_search.dataset import find_resume_column
from resume_search.extraction import extract_experience, extract_skills
from resume_search.text import has_words, normalize_text


@dataclass
class SearchIndex:
    """A fitted TF-IDF index over one dataset."""

    texts: list[str]
    categories: list[str]
    names: list[str]
    experience: list[int | None]
    vectorizer: Any = None
    matrix: Any = None
    extras: dict[str, Any] = field(default_factory=dict)

    @property
    def size(self) -> int:
        """Number of resumes in the index."""
        return len(self.texts)


def validate_job_title(job_title: str) -> str:
    """Return the normalised job title.

    Raises:
        ValueError: when the title is blank or has no words.
    """
    normalized = normalize_text(job_title)
    if not normalized:
        raise ValueError("Job title is required and cannot be blank.")
    if not has_words(normalized):
        raise ValueError("Job title must contain at least one usable word.")
    return normalized


def build_search_query(job_title: str, skills: list[str]) -> str:
    """Combine the job title and skills into one normalised query string."""
    pieces = [validate_job_title(job_title)]
    pieces.extend(normalize_text(skill) for skill in skills)
    return " ".join(piece for piece in pieces if piece)


def build_index(
    texts: list[str],
    categories: list[str] | None = None,
    names: list[str] | None = None,
) -> SearchIndex:
    """Fit a TF-IDF vectoriser over the resume texts."""
    from sklearn.feature_extraction.text import TfidfVectorizer

    safe_texts = ["" if text is None else str(text) for text in texts]
    count = len(safe_texts)
    index = SearchIndex(
        texts=safe_texts,
        categories=list(categories) if categories is not None else [""] * count,
        names=list(names) if names is not None else [""] * count,
        experience=[extract_experience(text) for text in safe_texts],
    )
    vectorizer = TfidfVectorizer(
        lowercase=True,
        preprocessor=normalize_text,
        token_pattern=r"(?u)\b\w+\b",
        stop_words="english",
        sublinear_tf=False,
    )
    try:
        index.matrix = vectorizer.fit_transform(safe_texts)
        index.vectorizer = vectorizer
    except ValueError:  # empty vocabulary: nothing searchable
        index.matrix = None
    return index


def build_index_from_dataframe(df: pd.DataFrame) -> SearchIndex:
    """Build an index from a validated resume dataframe."""
    resume_column = find_resume_column(df)
    texts = df[resume_column].fillna("").astype(str).tolist()
    categories = (
        df[CATEGORY_COLUMN].fillna("").astype(str).tolist() if CATEGORY_COLUMN in df.columns else None
    )
    names = df[NAME_COLUMN].fillna("").astype(str).tolist() if NAME_COLUMN in df.columns else None
    return build_index(texts, categories, names)


def rank(
    index: SearchIndex,
    search_query: str,
    skills: list[str],
    min_experience: int | None,
    limit: int,
) -> list[dict[str, Any]]:
    """Score every resume against the query and return the top ``limit`` rows."""
    if index.matrix is None or not index.texts:
        return []
    from sklearn.metrics.pairwise import linear_kernel

    query_vector = index.vectorizer.transform([search_query])
    scores = linear_kernel(query_vector, index.matrix).ravel()
    rows: list[dict[str, Any]] = []
    for position, score in enumerate(scores):
        text = index.texts[position]
        if not re.search(r"\w", text):
            continue
        experience = index.experience[position]
        if min_experience is not None and (experience is None or experience < min_experience):
            continue
        matched = extract_skills(text, skills) if skills else []
        rows.append({
            "original_index": position,
            "name": index.names[position],
            "resume_text": text,
            "category": index.categories[position],
            "score": float(score),
            "experience": experience,
            "matched_skills": matched,
            "missing_skills": [skill for skill in skills if skill not in matched],
        })
    rows.sort(key=lambda row: (-row["score"], row["original_index"]))
    return rows[:limit]


def search_index(
    index: SearchIndex,
    job_title: str,
    skills: list[str],
    min_experience: int | None,
    limit: int,
) -> dict[str, Any]:
    """Run one search against a prepared index."""
    if limit < 1:
        raise ValueError("Result limit must be at least 1.")
    started = time.perf_counter()
    unique_skills = list(dict.fromkeys(skills))
    search_query = build_search_query(job_title, unique_skills)
    results = rank(index, search_query, unique_skills, min_experience, limit)
    return {
        "results": results,
        "total_candidates": index.size,
        "search_query": search_query,
        "skills_requested": unique_skills,
        "min_experience": min_experience,
        "search_seconds": time.perf_counter() - started,
    }


def search_resumes(
    df: pd.DataFrame,
    job_title: str,
    skills: list[str],
    min_experience: int | None,
    limit: int,
) -> dict[str, Any]:
    """Build an index for ``df`` and run one search (convenience wrapper)."""
    if limit < 1:
        raise ValueError("Result limit must be at least 1.")
    return search_index(build_index_from_dataframe(df), job_title, skills, min_experience, limit)
