"""TF-IDF ranking of resumes against a role.

The index is built once per dataset (:func:`build_index`); every search then
only transforms the query (:func:`rank`), which keeps searches fast.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from resume_search.config import CATEGORY_COLUMN, MAX_JOB_DESCRIPTION_CHARS, NAME_COLUMN, TOP_TERMS
from resume_search.dataset import find_resume_column
from resume_search.extraction import extract_experience, extract_skills
from resume_search.text import has_words, normalize_text, word_count


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


def build_search_query(job_title: str, skills: list[str], job_description: str = "") -> str:
    """Combine the job title, skills and optional job description into one query.

    A job title is required unless a job description with words is supplied.
    """
    description = normalize_text(job_description[:MAX_JOB_DESCRIPTION_CHARS])
    if has_words(description) and not normalize_text(job_title):
        pieces = []
    elif not normalize_text(job_title):
        raise ValueError("Enter a job title or paste a job description.")
    else:
        pieces = [validate_job_title(job_title)]
    pieces.extend(normalize_text(skill) for skill in skills)
    if has_words(description):
        pieces.append(description)
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
        # Bandit B106 false positive: "token_pattern" is a word regex, not a password.
        token_pattern=r"(?u)\b\w+\b",  # nosec B106
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


def _query_vector(index: SearchIndex, search_query: str) -> Any:
    return index.vectorizer.transform([search_query])


def score_all(index: SearchIndex, search_query: str) -> Any:
    """Return the TF-IDF cosine score of every resume as a NumPy array (zeros if nothing is indexed)."""
    import numpy as np

    if index.matrix is None:
        return np.zeros(index.size)
    return np.asarray((index.matrix @ _query_vector(index, search_query).T).todense()).ravel()


def rank(
    index: SearchIndex,
    search_query: str,
    skills: list[str],
    min_experience: int | None,
    limit: int,
    include_unknown_experience: bool = False,
) -> list[dict[str, Any]]:
    """Score every resume against the query and return the top ``limit`` rows.

    Candidates below ``min_experience`` are dropped. Candidates whose experience
    was not detected are kept only when ``include_unknown_experience`` is True.
    """
    return _rank_with_count(index, search_query, skills, min_experience, limit, include_unknown_experience)[0]


def _rank_with_count(
    index: SearchIndex,
    search_query: str,
    skills: list[str],
    min_experience: int | None,
    limit: int,
    include_unknown_experience: bool,
) -> tuple[list[dict[str, Any]], int]:
    if index.matrix is None or not index.texts:
        return [], 0
    import numpy as np

    scores = score_all(index, search_query)
    if "usable" not in index.extras:
        index.extras["usable"] = np.array([has_words(text) for text in index.texts], dtype=bool)
    keep = index.extras["usable"]
    if min_experience is not None:
        experience_ok = np.array([
            (years is None and include_unknown_experience) or (years is not None and years >= min_experience)
            for years in index.experience
        ], dtype=bool)
        keep = keep & experience_ok
    candidates = np.flatnonzero(keep)
    matched_count = int(np.count_nonzero(scores[candidates] > 0))
    # Stable sort: highest score first, ties keep the original order.
    order = candidates[np.argsort(-scores[candidates], kind="stable")][:limit]
    rows = [_result_row(index, int(position), float(scores[position]), skills) for position in order]
    return rows, matched_count


def _result_row(index: SearchIndex, position: int, score: float, skills: list[str]) -> dict[str, Any]:
    text = index.texts[position]
    matched = extract_skills(text, skills) if skills else []
    return {
        "original_index": position,
        "name": index.names[position],
        "resume_text": text,
        "category": index.categories[position],
        "score": score,
        "experience": index.experience[position],
        "matched_skills": matched,
        "missing_skills": [skill for skill in skills if skill not in matched],
    }


def explain_score(
    index: SearchIndex, search_query: str, position: int, top_n: int = TOP_TERMS
) -> list[tuple[str, float]]:
    """Return the terms that contributed most to one resume's score.

    Cosine similarity of two L2-normalised TF-IDF vectors is the sum of the
    per-term products, so each product is that term's exact contribution.
    """
    if index.matrix is None:
        return []
    contributions = _query_vector(index, search_query).multiply(index.matrix[position]).tocoo()
    if "terms" not in index.extras:
        index.extras["terms"] = index.vectorizer.get_feature_names_out()
    terms = index.extras["terms"]
    pairs = sorted(
        ((str(terms[column]), float(value)) for column, value in zip(contributions.col, contributions.data, strict=True)),
        key=lambda pair: (-pair[1], pair[0]),
    )
    return [pair for pair in pairs if pair[1] > 0][:top_n]


def search_index(
    index: SearchIndex,
    job_title: str,
    skills: list[str],
    min_experience: int | None,
    limit: int,
    *,
    job_description: str = "",
    include_unknown_experience: bool = False,
) -> dict[str, Any]:
    """Run one search against a prepared index (only the query is transformed)."""
    if limit < 1:
        raise ValueError("Result limit must be at least 1.")
    started = time.perf_counter()
    unique_skills = list(dict.fromkeys(skill.strip() for skill in skills if skill.strip()))
    search_query = build_search_query(job_title, unique_skills, job_description)
    results, matched_count = _rank_with_count(
        index, search_query, unique_skills, min_experience, limit, include_unknown_experience
    )
    for row in results:
        row["top_terms"] = explain_score(index, search_query, row["original_index"])
    return {
        "results": results,
        "total_candidates": index.size,
        "matched_candidates": matched_count,
        "search_query": search_query,
        "skills_requested": unique_skills,
        "min_experience": min_experience,
        "search_seconds": time.perf_counter() - started,
    }


def match_resume_to_job(resume_text: str, job_description: str, skills: list[str] | None = None) -> dict[str, Any]:
    """Score one resume against one job description (the job-seeker check).

    Returns:
        ``score``, ``matched_skills``, ``missing_skills``, ``top_terms``,
        ``experience`` and ``word_count``.

    Raises:
        ValueError: when the resume or the job description has no words.
    """
    if not has_words(resume_text):
        raise ValueError("Add your resume (upload a file or paste the text) first.")
    if not has_words(job_description):
        raise ValueError("Paste the job description you want to compare against.")
    requested = list(dict.fromkeys(skill.strip() for skill in (skills or []) if skill.strip()))
    index = build_index([resume_text])
    query = build_search_query("", requested, job_description)
    score = float(score_all(index, query)[0])
    matched = extract_skills(resume_text, requested)
    return {
        "score": score,
        "matched_skills": matched,
        "missing_skills": [skill for skill in requested if skill not in matched],
        "top_terms": explain_score(index, query, 0),
        "experience": index.experience[0],
        "word_count": word_count(resume_text),
    }


def search_resumes(
    df: pd.DataFrame,
    job_title: str,
    skills: list[str],
    min_experience: int | None,
    limit: int,
    **options: Any,
) -> dict[str, Any]:
    """Build an index for ``df`` and run one search (convenience wrapper)."""
    if limit < 1:
        raise ValueError("Result limit must be at least 1.")
    return search_index(build_index_from_dataframe(df), job_title, skills, min_experience, limit, **options)
