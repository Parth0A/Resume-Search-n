"""Ranking-quality evaluation: metrics, baseline rankers and significance tests.

Used by ``scripts/evaluate.py``. Labels are graded: 0 = not relevant,
1 = relevant, 2 = highly relevant. Resumes without a label count as 0.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Callable, Sequence
from typing import Any

from resume_search.ranking import build_index, score_all
from resume_search.text import normalize_text

Ranker = Callable[[list[str], str], list[float]]
"""A ranker takes the resume texts and a query and returns one score per resume."""

_TOKEN = re.compile(r"\b\w+\b")


def tokenize(text: str) -> list[str]:
    """Lower-case word tokens without English stop words."""
    from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

    return [token for token in _TOKEN.findall(normalize_text(text)) if token not in ENGLISH_STOP_WORDS]


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------
def precision_at_k(ranked: Sequence[int], grades: dict[int, int], k: int) -> float:
    """Share of the top ``k`` results that are relevant (grade > 0)."""
    top = list(ranked)[:k]
    return sum(grades.get(item, 0) > 0 for item in top) / k if k else 0.0


def recall_at_k(ranked: Sequence[int], grades: dict[int, int], k: int) -> float:
    """Share of all relevant resumes that appear in the top ``k``."""
    relevant = {item for item, grade in grades.items() if grade > 0}
    if not relevant:
        return 0.0
    return len(relevant & set(list(ranked)[:k])) / len(relevant)


def reciprocal_rank(ranked: Sequence[int], grades: dict[int, int]) -> float:
    """1 / position of the first relevant result (0 when none is found)."""
    for position, item in enumerate(ranked, start=1):
        if grades.get(item, 0) > 0:
            return 1.0 / position
    return 0.0


def ndcg_at_k(ranked: Sequence[int], grades: dict[int, int], k: int) -> float:
    """Normalised discounted cumulative gain with gain 2^grade - 1."""
    def dcg(values: Sequence[int]) -> float:
        return sum((2**grade - 1) / math.log2(position + 2) for position, grade in enumerate(values[:k]))

    ideal = dcg(sorted(grades.values(), reverse=True))
    if ideal == 0:
        return 0.0
    return dcg([grades.get(item, 0) for item in ranked]) / ideal


# ---------------------------------------------------------------------------
# Rankers
# ---------------------------------------------------------------------------
def keyword_scores(texts: list[str], query: str) -> list[float]:
    """Baseline: how many times the query's words occur in each resume."""
    terms = set(tokenize(query))
    return [float(sum(count for token, count in Counter(tokenize(text)).items() if token in terms)) for text in texts]


def tfidf_scores(texts: list[str], query: str) -> list[float]:
    """The app's TF-IDF cosine similarity."""
    return [float(value) for value in score_all(build_index(texts), normalize_text(query))]


def bm25_scores(texts: list[str], query: str, k1: float = 1.5, b: float = 0.75) -> list[float]:
    """Okapi BM25 with the usual parameters."""
    documents = [tokenize(text) for text in texts]
    count = len(documents)
    if count == 0:
        return []
    average_length = sum(len(document) for document in documents) / count or 1.0
    frequencies = Counter(token for document in documents for token in set(document))
    terms = tokenize(query)
    scores: list[float] = []
    for document in documents:
        counts = Counter(document)
        score = 0.0
        for term in terms:
            tf = counts.get(term, 0)
            if not tf:
                continue
            idf = math.log(1 + (count - frequencies[term] + 0.5) / (frequencies[term] + 0.5))
            score += idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * len(document) / average_length))
        scores.append(score)
    return scores


def default_rankers() -> dict[str, Ranker]:
    """Keyword, TF-IDF and BM25 (hybrid is added by the caller when available)."""
    return {"keyword": keyword_scores, "tfidf": tfidf_scores, "bm25": bm25_scores}


def order_by_score(scores: Sequence[float]) -> list[int]:
    """Resume positions from highest to lowest score (ties keep the original order)."""
    return sorted(range(len(scores)), key=lambda position: (-scores[position], position))


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------
def evaluate(
    texts: list[str],
    labels: list[tuple[str, int, int]],
    k: int,
    rankers: dict[str, Ranker] | None = None,
) -> dict[str, Any]:
    """Score every ranker on every labelled query.

    Args:
        texts: resume texts; a label's ``resume_id`` is the index into this list.
        labels: ``(query, resume_id, grade)`` tuples.
        k: cut-off for Precision@K, Recall@K and NDCG@K.
        rankers: name -> ranker; defaults to :func:`default_rankers`.

    Returns:
        ``{"queries": [...], "per_query": {method: {metric: [values]}}, "summary": {method: {metric: mean}}}``
    """
    rankers = rankers or default_rankers()
    by_query: dict[str, dict[int, int]] = {}
    for query, resume_id, grade in labels:
        if not 0 <= resume_id < len(texts):
            raise ValueError(f"resume_id {resume_id} is outside the dataset (0..{len(texts) - 1}).")
        if grade not in (0, 1, 2):
            raise ValueError(f"grade must be 0, 1 or 2 (got {grade}).")
        by_query.setdefault(query, {})[resume_id] = grade
    queries = list(by_query)
    per_query: dict[str, dict[str, list[float]]] = {}
    for name, ranker in rankers.items():
        metrics: dict[str, list[float]] = {"precision": [], "recall": [], "mrr": [], "ndcg": []}
        for query in queries:
            ranked = order_by_score(ranker(texts, query))
            grades = by_query[query]
            metrics["precision"].append(precision_at_k(ranked, grades, k))
            metrics["recall"].append(recall_at_k(ranked, grades, k))
            metrics["mrr"].append(reciprocal_rank(ranked, grades))
            metrics["ndcg"].append(ndcg_at_k(ranked, grades, k))
        per_query[name] = metrics
    summary = {
        name: {metric: sum(values) / len(values) if values else 0.0 for metric, values in metrics.items()}
        for name, metrics in per_query.items()
    }
    return {"queries": queries, "per_query": per_query, "summary": summary}


def wilcoxon_vs(per_query: dict[str, dict[str, list[float]]], baseline: str = "tfidf",
                metric: str = "ndcg") -> dict[str, dict[str, float | str]]:
    """Paired Wilcoxon signed-rank test of ``baseline`` against every other method.

    Returns:
        method -> {"statistic", "p_value", "note"}. When all paired differences are
        zero the test is undefined; p = 1.0 is reported with a note.
    """
    from scipy.stats import wilcoxon

    results: dict[str, dict[str, float | str]] = {}
    base = per_query[baseline][metric]
    for name, metrics in per_query.items():
        if name == baseline:
            continue
        other = metrics[metric]
        if all(abs(a - b) < 1e-12 for a, b in zip(base, other, strict=True)):
            results[name] = {"statistic": 0.0, "p_value": 1.0, "note": "identical scores"}
            continue
        test = wilcoxon(base, other, zero_method="zsplit")
        note = "few queries; low power" if len(base) < 10 else ""
        results[name] = {"statistic": float(test.statistic), "p_value": float(test.pvalue), "note": note}
    return results
