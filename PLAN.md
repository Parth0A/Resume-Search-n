# PLAN — Resume Search overhaul

Source of truth: `C:\Parth\CLAUDE_CODE_MASTER_PROMPT.md` (Tasks 1–8).

1. **Fix ranking bug** — shared lowercase normalisation for query and resumes;
   regression test with capitalised resumes.
2. **Structure** — split `backend.py`, `auth.py`, `ai_features.py` into the
   `resume_search/` package; split `app.py` into `ui/` modules plus one
   `ui/styles.css`; keep old tests in equivalent form; ruff + vulture clean.
3. **UI design** — design tokens, components, branding assets, login page,
   sidebar navigation, header with step tracker, workspace cards, results,
   other pages, speed (cached index, session state), small screens.
4. **Security** — SECURITY_REVIEW.md, PBKDF2 600k + rehash, lockout, session
   timeout, password rules, upload validation, CSV formula-injection guard,
   logging, DB permissions, Gemini key handling, bandit + pip-audit.
5. **Tests & quality** — per-module tests, ≥85 % coverage, ruff clean,
   type hints/docstrings, pre-commit, GitHub Actions CI.
6. **Open-source files** — README, per-folder READMEs, architecture doc,
   licence and community files, requirements, pyproject, templates, sample
   data, Dockerfile.
7. **Features a–i** — skill aliases, experience detection, why-this-score,
   job-description ranking, file uploads, blind screening, evaluation script,
   roles and shortlists, optional hybrid ranking.
8. **Final verification** — run every tool, fresh-venv start, report table.

Environment notes: Python 3.12 and Git were installed with winget for this
work (they were not on the machine). The project venv is `.venv`.
