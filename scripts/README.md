# scripts

| File | What it does |
|------|--------------|
| `make_sample_data.py` | Writes the synthetic `data/sample_resumes.csv` (fixed random seed). |
| `evaluate.py` | Measures ranking quality on a labelled CSV. |

## evaluate.py

```bash
python scripts/evaluate.py --resumes data/sample_resumes.csv --labels data/sample_relevance.csv --k 5
```

The labels file has the columns `query`, `resume_id` (the 0-based row number in the resume CSV) and
`grade` (0 = not relevant, 1 = relevant, 2 = highly relevant). The script reports Precision@K,
Recall@K, MRR and NDCG@K for keyword, TF-IDF, BM25 and (when `sentence-transformers` is installed)
hybrid ranking. It then runs a paired Wilcoxon signed-rank test on per-query NDCG, comparing TF-IDF
with each other method.
