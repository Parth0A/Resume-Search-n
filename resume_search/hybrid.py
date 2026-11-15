"""Optional semantic ranking with sentence-transformers.

Hybrid score = ``HYBRID_TFIDF_WEIGHT`` × TF-IDF + (1 − weight) × semantic cosine.
The model (``all-MiniLM-L6-v2``) is loaded lazily, once per process, and resume
embeddings are cached on the search index, so only the query is embedded per
search. TF-IDF stays the default; nothing here runs unless hybrid is chosen.
"""

from __future__ import annotations

import importlib.util
from functools import lru_cache
from typing import Any

from resume_search.config import HYBRID_MODEL_NAME, HYBRID_TFIDF_WEIGHT


def is_available() -> bool:
    """True when the optional ``sentence-transformers`` package is installed."""
    return importlib.util.find_spec("sentence_transformers") is not None


@lru_cache(maxsize=1)
def _load_model() -> Any:
    if not is_available():
        raise ValueError(
            "Hybrid ranking needs the optional 'sentence-transformers' package "
            "(pip install sentence-transformers)."
        )
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(HYBRID_MODEL_NAME)


def embed(texts: list[str]) -> Any:
    """Return L2-normalised embeddings (one row per text) as a NumPy array."""
    import numpy as np

    vectors = np.asarray(
        _load_model().encode(list(texts), convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False),
        dtype=float,
    )
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vectors / norms


def semantic_scores(document_embeddings: Any, query: str) -> Any:
    """Cosine similarity of the query with every document, clipped to 0..1."""
    import numpy as np

    return np.clip(document_embeddings @ embed([query])[0], 0.0, 1.0)


def combine(tfidf: Any, semantic: Any, weight: float = HYBRID_TFIDF_WEIGHT) -> Any:
    """Weighted mix of TF-IDF and semantic scores."""
    return weight * tfidf + (1.0 - weight) * semantic


def hybrid_scores(texts: list[str], query: str) -> list[float]:
    """Ranker for ``scripts/evaluate.py``: hybrid scores for raw texts."""
    from resume_search.ranking import build_index, score_all
    from resume_search.text import normalize_text

    tfidf = score_all(build_index(texts), normalize_text(query))
    return [float(value) for value in combine(tfidf, semantic_scores(embed(texts), query))]
