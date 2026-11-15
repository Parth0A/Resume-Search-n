"""Tests for optional hybrid ranking. The sentence-transformers model is always mocked."""

from __future__ import annotations

import numpy as np
import pytest

from resume_search import hybrid
from resume_search.ranking import build_index, search_index

VOCAB = ["python", "developer", "chef", "cooking", "software", "engineer", "coder"]
SYNONYMS = {"coder": "developer", "software": "python"}


class FakeModel:
    """Tiny deterministic 'embedding': bag of words over VOCAB with a few synonyms."""

    calls = 0

    def encode(self, texts, **kwargs):
        FakeModel.calls += 1
        rows = []
        for text in texts:
            words = [SYNONYMS.get(word, word) for word in text.lower().replace(",", " ").split()]
            rows.append([float(words.count(term)) for term in VOCAB])
        return np.array(rows)


@pytest.fixture
def fake_model(monkeypatch):
    FakeModel.calls = 0
    monkeypatch.setattr(hybrid, "_load_model", lambda: FakeModel())
    return FakeModel


def test_combine_weights():
    assert hybrid.combine(np.array([1.0]), np.array([0.0]))[0] == pytest.approx(0.5)
    assert hybrid.combine(np.array([0.2]), np.array([0.6]), weight=0.25)[0] == pytest.approx(0.5)


def test_embed_normalises_and_handles_zero_vectors(fake_model):
    vectors = hybrid.embed(["python python developer", "unknown words"])
    assert np.linalg.norm(vectors[0]) == pytest.approx(1.0)
    assert np.all(vectors[1] == 0)


def test_hybrid_search_finds_synonym_match(fake_model):
    texts = ["Experienced coder building tools", "Chef cooking pasta"]
    index = build_index(texts)
    tfidf = search_index(index, "developer", [], None, 2)
    mixed = search_index(index, "developer", [], None, 2, method="hybrid")
    assert tfidf["results"][0]["score"] == 0.0  # no shared words
    assert mixed["method"] == "hybrid"
    assert mixed["results"][0]["original_index"] == 0
    assert mixed["results"][0]["score"] == pytest.approx(0.5)  # 0.5 × 0 + 0.5 × 1
    assert mixed["matched_candidates"] == 0  # "matched" still means shared terms


def test_resume_embeddings_are_cached(fake_model):
    index = build_index(["python developer", "chef"])
    search_index(index, "python", [], None, 2, method="hybrid")
    search_index(index, "chef", [], None, 2, method="hybrid")
    assert fake_model.calls == 3  # resumes once + one call per query


def test_hybrid_scores_ranker(fake_model):
    scores = hybrid.hybrid_scores(["python developer", "chef cooking"], "python developer")
    assert scores[0] > scores[1]


def test_unknown_method_rejected():
    with pytest.raises(ValueError, match="Unknown ranking method"):
        search_index(build_index(["python"]), "python", [], None, 1, method="magic")


def test_missing_package_gives_clear_error(monkeypatch):
    hybrid._load_model.cache_clear()
    monkeypatch.setattr(hybrid, "is_available", lambda: False)
    with pytest.raises(ValueError, match="pip install sentence-transformers"):
        hybrid._load_model()
    hybrid._load_model.cache_clear()


def test_is_available_returns_bool():
    assert isinstance(hybrid.is_available(), bool)
