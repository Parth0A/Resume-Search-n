# tests

Run with `pytest -q` (add `--cov=resume_search` for coverage). Tests use synthetic data, a
temporary SQLite database (`temp_db` fixture) and never call the network.

| File | Covers |
|------|--------|
| `conftest.py` | `temp_db` fixture pointing `RESUME_SEARCH_DB` at a temporary file. |
| `test_text.py` | Normalisation, word helpers, contact redaction. |
| `test_dataset.py` | Upload validation, CSV reading, column detection, document reading. |
| `test_extraction.py` | Skill parsing/matching (aliases, boundaries) and experience detection. |
| `test_ranking.py` | Index, ranking, filters, job descriptions, score explanations, job-seeker check, mixed-case regression. |
| `test_hybrid.py` | Optional hybrid ranking with a fake embedding model (no download). |
| `test_export.py` | Export tables, blind export, formula-injection protection. |
| `test_auth.py` | Register, login, wrong password, duplicates, lockout, re-hash, schema upgrade. |
| `test_shortlists.py` | Shortlists, per-user isolation, clearing data, DB rollback. |
| `test_ai_features.py` | Gemini tools with a fake client: prompts, tag neutralising, reply validation. |
| `test_evaluation.py` | Ranking metrics and the evaluation script. |
| `test_app_smoke.py` | The Streamlit app starts and every page renders (Streamlit AppTest). |
