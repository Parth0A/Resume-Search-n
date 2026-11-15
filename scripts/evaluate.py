"""Evaluate ranking quality on a labelled CSV.

Usage:
    python scripts/evaluate.py --resumes data/sample_resumes.csv --labels data/sample_relevance.csv --k 5

The labels CSV needs the columns: query, resume_id (0-based row in the resume CSV), grade (0, 1 or 2).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402

from resume_search.dataset import find_resume_column, load_resumes  # noqa: E402
from resume_search.evaluation import default_rankers, evaluate, wilcoxon_vs  # noqa: E402


def _load_labels(path: Path) -> list[tuple[str, int, int]]:
    labels = pd.read_csv(path)
    missing = {"query", "resume_id", "grade"} - set(labels.columns)
    if missing:
        raise SystemExit(f"Labels file is missing columns: {', '.join(sorted(missing))}")
    return [(str(row.query), int(row.resume_id), int(row.grade)) for row in labels.itertuples()]


def _rankers() -> dict:
    rankers = default_rankers()
    try:
        from resume_search.hybrid import hybrid_scores, is_available
    except ImportError:  # hybrid module not present
        return rankers
    if is_available():
        rankers["hybrid"] = hybrid_scores
    else:
        print("Hybrid ranking skipped: sentence-transformers is not installed.\n")
    return rankers


def main(argv: list[str] | None = None) -> int:
    """Run the evaluation and print a summary table and significance tests."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--resumes", type=Path, required=True, help="Resume CSV")
    parser.add_argument("--labels", type=Path, required=True, help="Labels CSV (query, resume_id, grade)")
    parser.add_argument("--k", type=int, default=5, help="Cut-off for P@K, R@K and NDCG@K (default 5)")
    args = parser.parse_args(argv)

    df = load_resumes(args.resumes.read_bytes())
    texts = df[find_resume_column(df)].fillna("").astype(str).tolist()
    report = evaluate(texts, _load_labels(args.labels), args.k, _rankers())

    print(f"{len(report['queries'])} queries, {len(texts)} resumes, K = {args.k}\n")
    header = f"{'method':<10}{'P@K':>8}{'R@K':>8}{'MRR':>8}{'NDCG@K':>9}"
    print(header)
    print("-" * len(header))
    for name, metrics in report["summary"].items():
        print(f"{name:<10}{metrics['precision']:>8.3f}{metrics['recall']:>8.3f}"
              f"{metrics['mrr']:>8.3f}{metrics['ndcg']:>9.3f}")

    print("\nPaired Wilcoxon signed-rank test on per-query NDCG@K (TF-IDF vs each method):")
    for name, result in wilcoxon_vs(report["per_query"]).items():
        note = f"  ({result['note']})" if result["note"] else ""
        print(f"  tfidf vs {name:<8} W = {result['statistic']:.1f}  p = {result['p_value']:.4f}{note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
