# CLAUDE.md — working rules for Resume Search

Resume Search ranks resumes from a CSV (or single PDF/DOCX/TXT files) against a
role using TF-IDF cosine similarity, with local SQLite accounts and optional
Google Gemini tools, served by Streamlit.

## Process rules
- Read PLAN.md and PROGRESS.md first. Continue from the first unchecked item in
  PROGRESS.md; never restart finished work.
- One small change at a time. Run `python -m pytest -q` after each change and
  fix any failure before moving on. Never delete or weaken a test to make it pass.
- After each numbered task: confirm the app imports (`python -c "import app"`),
  tick PROGRESS.md, and make a git commit with a clear message.
- Never claim something is done without running the command that proves it.
- Add a dependency only when a task names it. Never rewrite git history.
- Note every assumption or Streamlit limitation in PROGRESS.md.

## Architecture
- `resume_search/` — core package (config, text, dataset, extraction, ranking,
  export, auth, ai_features, shortlists, evaluation helpers). It must **never**
  import `streamlit`.
- `ui/` — Streamlit screens and helpers. UI code calls only *public* functions
  of `resume_search` (no leading underscore imports).
- `app.py` — thin entry point: page config, CSS, routing.
- All constants live in `resume_search/config.py`.
- All CSS lives in **one** file: `ui/styles.css`. No inline `<style>` blocks
  elsewhere.
- `assets/` logo files, `tests/` one file per core module, `data/` synthetic
  sample data, `docs/` documentation, `scripts/` tooling.

## Security rules
- Never print, log or commit secrets (.env, API keys, *.db, real resumes).
- Never put unescaped user or resume text into `unsafe_allow_html`; HTML
  helpers in `ui/components.py` always use `html.escape`.
- Parameterized SQL only. Passwords: PBKDF2-HMAC-SHA256, 600,000 iterations,
  per-user iteration count, re-hash on login; lockout after 5 failures.
- Use the `logging` module; never log passwords, resume text or e-mails.
- CSV exports are protected against formula injection.
- Gemini key only from environment / `st.secrets`; one resume sent per explicit
  click; JSON replies validated.
