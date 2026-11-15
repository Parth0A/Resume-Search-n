"""Tests for resume_search.evaluation and scripts/evaluate.py."""

from __future__ import annotations

import importlib.util
import math
from pathlib import Path

import pytest

from resume_search.evaluation import (
    bm25_scores,
    evaluate,
    keyword_scores,
    ndcg_at_k,
    order_by_score,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
    tfidf_scores,
    tokenize,
    wilcoxon_vs,
)

ROOT = Path(__file__).resolve().parent.parent
GRADES = {0: 2, 2: 1, 5: 0}


def test_precision_recall_mrr():
    ranked = [3, 0, 4, 2]
    assert precision_at_k(ranked, GRADES, 2) == 0.5
    assert precision_at_k(ranked, GRADES, 0) == 0.0
    assert recall_at_k(ranked, GRADES, 2) == 0.5
    assert recall_at_k(ranked, GRADES, 4) == 1.0
    assert recall_at_k(ranked, {1: 0}, 3) == 0.0
    assert reciprocal_rank(ranked, GRADES) == 0.5
    assert reciprocal_rank([9, 8], GRADES) == 0.0


def test_ndcg():
    assert ndcg_at_k([0, 2, 5], GRADES, 3) == pytest.approx(1.0)
    worse = ndcg_at_k([2, 0], GRADES, 2)
    expected = (1 + 3 / math.log2(3)) / (3 + 1 / math.log2(3))
    assert worse == pytest.approx(expected)
    assert ndcg_at_k([1, 2], {7: 0}, 2) == 0.0


def test_rankers_prefer_the_matching_resume():
    texts = ["Python developer Django APIs", "Chef cooking pasta", "Java developer Spring"]
    for ranker in (keyword_scores, tfidf_scores, bm25_scores):
        assert order_by_score(ranker(texts, "Python Django developer"))[0] == 0
    assert bm25_scores([], "python") == []
    assert tokenize("The Python AND the SQL") == ["python", "sql"]


def test_order_by_score_is_stable():
    assert order_by_score([0.5, 0.9, 0.5]) == [1, 0, 2]


def test_evaluate_and_wilcoxon():
    texts = ["python django", "react javascript", "python flask", "java spring"]
    labels = [("python", 0, 2), ("python", 2, 1), ("react", 1, 2), ("java", 3, 2)]
    report = evaluate(texts, labels, k=2)
    assert report["queries"] == ["python", "react", "java"]
    assert set(report["summary"]) == {"keyword", "tfidf", "bm25"}
    assert report["summary"]["tfidf"]["mrr"] == 1.0
    tests = wilcoxon_vs(report["per_query"])
    assert set(tests) == {"keyword", "bm25"}
    assert all(0.0 <= result["p_value"] <= 1.0 for result in tests.values())


def test_wilcoxon_with_differences():
    per_query = {"tfidf": {"ndcg": [0.9, 0.8, 0.7, 0.95, 0.85, 0.6]},
                 "keyword": {"ndcg": [0.5, 0.4, 0.6, 0.3, 0.2, 0.1]}}
    result = wilcoxon_vs(per_query)["keyword"]
    assert result["p_value"] < 0.05
    assert result["note"] == "few queries; low power"


@pytest.mark.parametrize(("labels", "message"), [
    ([("q", 9, 1)], "outside the dataset"),
    ([("q", 0, 3)], "grade must be"),
])
def test_evaluate_validates_labels(labels, message):
    with pytest.raises(ValueError, match=message):
        evaluate(["a resume"], labels, k=1)


def test_evaluate_script_runs_on_sample_data(capsys):
    spec = importlib.util.spec_from_file_location("evaluate_script", ROOT / "scripts" / "evaluate.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    code = module.main(["--resumes", str(ROOT / "data" / "sample_resumes.csv"),
                        "--labels", str(ROOT / "data" / "sample_relevance.csv"), "--k", "5"])
    output = capsys.readouterr().out
    assert code == 0
    assert "tfidf" in output and "bm25" in output and "Wilcoxon" in output
