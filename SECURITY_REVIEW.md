# Security review — Resume Search

Scope: every Python file in the original project (`app.py`, `backend.py`, `auth.py`,
`ai_features.py`) and the restructured code in `resume_search/`, `ui/` and `app.py`.
Date: 2026-11-15. Tools: manual review, `bandit -r resume_search ui app.py`,
`pip-audit -r requirements.txt`, git-history secret scan.

| # | Finding | Severity | File (original) | Fix | Status |
|---|---------|----------|-----------------|-----|--------|
| 1 | PBKDF2 used 310,000 iterations, fixed for all users, so it could never be raised safely. | Medium | `auth.py` | 600,000 iterations; count stored per user (`users.iterations`); older hashes re-hashed after a successful sign-in. | Fixed — `resume_search/auth.py` |
| 2 | No limit on failed sign-ins (online password guessing). | High | `auth.py` | `login_attempts` table; 5 failures lock the e-mail for 15 minutes. Unknown e-mails are locked too. | Fixed |
| 3 | Unknown e-mails returned faster than wrong passwords (timing account enumeration). | Low | `auth.py` | A dummy PBKDF2 hash is computed for unknown e-mails; both cases return the same message. | Fixed |
| 4 | Password rules only checked length ≥ 8; very long passwords allowed (CPU cost). | Medium | `auth.py` | Minimum 8, maximum 1,024 characters, common-password list rejected. | Fixed |
| 5 | No session timeout; sign-out left dataset, results and AI output in the session. | Medium | `app.py` | 30-minute inactivity timeout; sign-out clears the whole session; "Clear my data" on the Privacy page. | Fixed — `ui/state.py`, `ui/profile_view.py` |
| 6 | Upload type and size were only checked after reading the whole file; limit was 1 GB. | Medium | `backend.py`, `app.py` | `validate_upload()` checks extension and size before parsing; limit 200 MB in code and `.streamlit/config.toml`; only needed columns are parsed. | Fixed — `resume_search/dataset.py` |
| 7 | CSV exports could contain cells starting with `=`, `+`, `-`, `@` (spreadsheet formula injection from resume text, names or categories). | High | `backend.py` | `protect_formula()` / `to_safe_csv()` prefix such cells (and headers) with `'`; used for results and shortlist exports. | Fixed — `resume_search/export.py` |
| 8 | Resume/CSV text placed in Markdown labels (`st.expander`, `st.markdown`) could inject links or images. | Low | `app.py` | `components.md()` escapes Markdown for CSV/user text; HTML helpers use `html.escape`; AI summaries are shown with `st.text`. | Fixed — `ui/components.py` |
| 9 | `unsafe_allow_html` used for many blocks. | Info | `app.py` | Every HTML block is built by helpers in `ui/components.py` that escape all dynamic text; static markup only otherwise. | Verified |
| 10 | Database file created with default permissions; path not documented. | Low | `auth.py` | Path from `RESUME_SEARCH_DB`; new files get mode `0600` where the OS supports it (no-op on Windows ACLs). | Fixed — `resume_search/db.py` |
| 11 | No logging; errors swallowed silently. | Low | all | `logging` module; unexpected errors are logged with stack traces server-side; users see friendly messages. Logs never include e-mails, passwords or resume text (user ids only). | Fixed |
| 12 | Gemini key only read from `.env`; prompt wrapper tags could be closed by resume text (`</resume>`); replies only checked to be a dict. | Medium | `ai_features.py` | Key from Streamlit secrets or environment only; tag-like text in untrusted input is neutralised; each reply is validated against an expected key/type schema. One selected resume (contact details hidden) is sent only after an explicit click, with a notice. | Fixed — `resume_search/ai_features.py`, `ui/ai_view.py` |
| 13 | Shortlists did not exist; any future per-user data needs isolation. | Info | — | Every shortlist query filters by `user_id`; resume text is never stored. | Implemented — `resume_search/shortlists.py` |
| 14 | `.gitignore` did not cover all secrets/data (`.env.*`, `secrets.toml`, `*.sqlite`, caches). | Low | `.gitignore` | Extended; only `data/sample_resumes.csv` (synthetic) is committable. | Fixed |
| 15 | Registration reveals whether an e-mail already has an account. | Low | `auth.py` | Accepted: a local, single-organisation tool; sign-in itself does not reveal accounts. Documented here. | Accepted risk |
| 16 | Bandit B106 on `token_pattern=r"(?u)\b\w+\b"`. | Info | `resume_search/ranking.py` | False positive (a tokenizer regex). Marked `# nosec B106` with an explanation. | Documented |
| 17 | Large CSVs are held in memory; a 200 MB file can use several GB of RAM. | Low | `dataset.py` | Size limit, `usecols`, one parse per file. Deploy with enough memory or lower `maxUploadSize`. | Documented |

## Tool results (2026-11-15)

- `bandit -r resume_search ui app.py`: no issues after the B106 false positive was marked.
- `pip-audit -r requirements.txt`: "No known vulnerabilities found".
- Git history: the repository was initialised for this work; a search of every commit for API-key,
  private-key and password patterns found only placeholder text (`GEMINI_API_KEY=your_key…`).
  The original zip contains only `.env.example` (no `.env`, no database). **No leaked secrets found.**
