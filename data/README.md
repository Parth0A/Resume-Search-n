# data

| File | What it is |
|------|------------|
| `sample_resumes.csv` | 40 **synthetic** resumes (no real people) with `Name`, `Category` and `Resume_str` columns. Mixed upper/lower case on purpose, with varied experience phrases and fake contact details for testing blind screening. Regenerate with `python scripts/make_sample_data.py data/sample_resumes.csv`. |
| `sample_relevance.csv` | Synthetic relevance labels (`query`, `resume_id`, `grade` 0/1/2) for `scripts/evaluate.py`. |

Do not commit real resumes. Other files in this folder are ignored by git.
