# resume_search — core package

Pure Python logic with **no Streamlit import**, so it can be tested and reused anywhere.

| File | What it does |
|------|--------------|
| `__init__.py` | Package marker; exposes `__version__`. |
| `config.py` | Every constant: column names, limits, skill lists and aliases, security settings, DB path, Gemini defaults. |
| `text.py` | The single text normaliser, word helpers and contact-detail redaction (blind screening). |
| `dataset.py` | Upload validation, the single CSV reader (needed columns only), dataset validation and PDF/DOCX/TXT reading. |
| `extraction.py` | Skill parsing and matching (with aliases and safe boundaries) and experience detection. |
| `ranking.py` | Builds the TF-IDF index once per dataset, ranks resumes, explains scores, supports job descriptions and hybrid mode. |
| `hybrid.py` | Optional sentence-transformers embeddings for hybrid ranking (lazy, cached). |
| `evaluation.py` | Ranking-quality metrics (Precision@K, Recall@K, MRR, NDCG) and baseline rankers used by `scripts/evaluate.py`. |
| `export.py` | Result tables and formula-safe CSV export. |
| `db.py` | SQLite connection helper (commit/rollback, owner-only file permissions). |
| `auth.py` | Accounts: PBKDF2 hashing with per-user iterations and re-hashing, lockout, password rules. |
| `shortlists.py` | Per-user saved shortlists. |
| `ai_features.py` | Optional Gemini tools with prompt-injection defences and reply validation. |
