# PROGRESS

## Setup
- [x] Read every file
- [x] CLAUDE.md, PLAN.md, PROGRESS.md created
- [x] git repository initialised, baseline committed

## Task 1 â€” Fix the main bug
- [x] Shared normalisation for query and resumes (lowercase=True)
- [x] Regression test: capitalised resumes, match ranks first, score > 0.3

## Task 2 â€” Structure
- [x] resume_search/ package (config, text, dataset, extraction, ranking, export, auth, ai_features), no streamlit import
- [x] ui/ folder with theme.py + the single styles.css (all inline CSS merged). The remaining ui/ screen modules
      are created in Task 3 together with the redesign, so the old screens are not written twice (see notes).
- [x] app.py thin entry point (completed in Task 3 with the ui/ screens)
- [x] assets/, tests/ per module, data/, docs/, scripts/
- [x] No duplicate code (one normaliser, one CSV reader, one constants file, one CSS file)
- [x] ruff check . clean; vulture clean
- [x] UI uses only public core functions
- [x] Caches/stray files removed; old tests kept (split into test_text/dataset/extraction/ranking/export) and passing

## Task 3 â€” UI design
- [x] 3.1 Design tokens, fonts, .streamlit/config.toml, hide menu/footer/deploy
- [x] 3.2 Components (buttons, chips, relevance bar, avatar, card header, escaping)
- [x] 3.3 Logo and branding assets, favicon, page config
- [x] 3.4 Login page
- [x] 3.5 Sidebar navigation and profile card
- [x] 3.6 Header, step tracker, workspace cards, results, other pages
- [x] 3.7 Speed and loading (index built once per file, query-only searches, session-state caching, lazy imports)
- [x] 3.8 Small screens and accessibility
- [x] 3.9 Differences from the design listed below

## Task 4 â€” Security
- [x] SECURITY_REVIEW.md written, every finding fixed (one accepted risk documented: registration reveals existing e-mails)
- [x] PBKDF2 600k, iterations per user, rehash on login
- [x] Lockout 15 min after 5 failures; same error for unknown e-mail / wrong password
- [x] 30 min inactivity timeout; sign-out clears session; Clear my data
- [x] Password rules (8+ chars, common passwords rejected)
- [x] Upload type/size validated before parsing
- [x] CSV formula-injection protection
- [x] No unescaped user text in unsafe_allow_html (plus Markdown escaping for labels)
- [x] Parameterised SQL; DB path env var; owner-only permissions; logging without PII
- [x] Gemini key from env/st.secrets; one resume per click; JSON validated
- [x] pip-audit and bandit run, findings fixed or documented
- [x] .gitignore complete; git history searched for secrets (none found)

## Task 5 â€” Tests and quality
- [x] Tests per core module (text, dataset, extraction, ranking, export, auth, shortlists/db, ai_features mocked) + app smoke tests
- [x] Coverage >= 85 % (98.6 %); ruff clean
- [x] Type hints and docstrings on public functions
- [x] .pre-commit-config.yaml
- [x] .github/workflows/ci.yml (3.10â€“3.12) â€” written, not run (no GitHub remote here)

## Task 6 â€” Open-source files
- [x] README.md (logo, all sections) â€” written for the finished v1.0, so it already lists the Task 7 features
- [x] README.md per folder (resume_search, ui, tests, assets, data, docs, scripts)
- [x] docs/architecture.md with Mermaid
- [x] LICENSE, SECURITY.md, CONTRIBUTING.md, CODE_OF_CONDUCT.md (short original text linking the Contributor Covenant 2.1), CHANGELOG.md
- [x] .env.example, requirements.txt, requirements-dev.txt, pyproject.toml
- [x] Issue and PR templates
- [x] Deployment notes and How to cite
- [x] data/sample_resumes.csv (40 synthetic), Dockerfile non-root (written; Docker is not installed here, so the image was not built)

## Task 7 â€” Features
- [x] a. Skill aliases and boundary rules
- [ ] b. Better experience detection + include-unknown toggle
- [ ] c. Why this score (top 5 terms)
- [ ] d. Paste job description
- [ ] e. PDF/DOCX/TXT upload, short-file warning
- [ ] f. Blind screening
- [ ] g. scripts/evaluate.py
- [ ] h. Roles and saved shortlists
- [ ] i. Optional hybrid ranking

## Task 8 â€” Final verification
- [ ] pytest --cov, ruff, bandit, pip-audit, vulture
- [ ] Fresh venv start with sample data
- [ ] Report table

## Notes, assumptions and differences
- Python 3.12 and Git were not installed; installed with winget (user approved).
- The design images `docs/design/resume_search_ui_design.png` and
  `docs/design/resume_search_logo_in_app.png` do not exist anywhere on disk, so
  Task 3 follows the written spec only.
- `assets/` did not exist; only `C:\Parth\resume_search_icon.svg` was provided.
  The PNG assets are generated from that SVG (user approved) with headless Chrome + Pillow.
- Task 2 / Task 3 ordering: the ui/ screen modules were written once, in Task 3, instead of first
  splitting the old screens and then rewriting them.
- Some Task 7 plumbing the Task 3 design needs landed in Task 3: score explanation (7c core), job
  description in the query (7d core), "Include unknown experience" toggle (7b toggle), blind screening
  of display/export (7f), saved shortlists storage and page (7h recruiter part). Task 7 completes and
  tests the rest.

### Task 3 â€” where the UI differs from the written design (Streamlit limits)
- Ranked table is an interactive `st.dataframe` (row click selects the candidate). Its selected-row
  style is Streamlit's own, not `#F5F7FF` with a 3px indigo edge; the candidate name and job title are
  separate columns instead of two lines in one cell; matched skills use the dataframe list style, not
  green chips; the relevance bar is the dataframe progress column. Chips, bar and colours match the spec
  in the candidate panel and Profiles tab.
- The "Export CSV" button sits above the tabs on the right, not inside the tab strip.
- The search card adds a small "Show" (number of results) select next to minimum experience so the
  existing results-limit feature keeps working.
- Toggle help text is a caption under the toggle row (tooltips made the labels too narrow).
- Upload progress uses `st.status` while running; once finished a static list with green ticks and
  timings is shown. The first upload's "Building search index" time includes the one-off scikit-learn
  import (~3 s); later uploads are fast.
- The sidebar profile card is pushed to the bottom with CSS (`margin-top: auto`); on very short
  windows it simply follows the menu.
- Account type is chosen only when creating an account (sign-in uses the stored role) instead of on
  both forms.
- Visual check done in the in-app browser at 1440 px (login, all five pages, search, shortlist) and at
  375 px for the login page. The signed-in pages at phone width were not screenshot-checked because
  the browser pane was closed during testing.
