# PROGRESS

## Setup
- [x] Read every file
- [x] CLAUDE.md, PLAN.md, PROGRESS.md created
- [x] git repository initialised, baseline committed

## Task 1 — Fix the main bug
- [x] Shared normalisation for query and resumes (lowercase=True)
- [x] Regression test: capitalised resumes, match ranks first, score > 0.3

## Task 2 — Structure
- [x] resume_search/ package (config, text, dataset, extraction, ranking, export, auth, ai_features), no streamlit import
- [x] ui/ folder with theme.py + the single styles.css (all inline CSS merged). The remaining ui/ screen modules
      are created in Task 3 together with the redesign, so the old screens are not written twice (see notes).
- [ ] app.py thin entry point (completed in Task 3 with the ui/ screens)
- [x] assets/, tests/ per module, data/, docs/, scripts/
- [x] No duplicate code (one normaliser, one CSV reader, one constants file, one CSS file)
- [x] ruff check . clean; vulture clean
- [x] UI uses only public core functions
- [x] Caches/stray files removed; old tests kept (split into test_text/dataset/extraction/ranking/export) and passing

## Task 3 — UI design
- [ ] 3.1 Design tokens, fonts, .streamlit/config.toml, hide menu/footer/deploy
- [ ] 3.2 Components (buttons, chips, relevance bar, avatar, card header, escaping)
- [ ] 3.3 Logo and branding assets, favicon, page config
- [ ] 3.4 Login page
- [ ] 3.5 Sidebar navigation and profile card
- [ ] 3.6 Header, step tracker, workspace cards, results, other pages
- [ ] 3.7 Speed and loading
- [ ] 3.8 Small screens and accessibility
- [ ] 3.9 Differences from the design listed below

## Task 4 — Security
- [ ] SECURITY_REVIEW.md written, every finding fixed
- [ ] PBKDF2 600k, iterations per user, rehash on login
- [ ] Lockout 15 min after 5 failures; same error for unknown e-mail / wrong password
- [ ] 30 min inactivity timeout; sign-out clears session; Clear my data
- [ ] Password rules (8+ chars, common passwords rejected)
- [ ] Upload type/size validated before parsing
- [ ] CSV formula-injection protection
- [ ] No unescaped user text in unsafe_allow_html
- [ ] Parameterised SQL; DB path env var; owner-only permissions; logging without PII
- [ ] Gemini key from env/st.secrets; one resume per click; JSON validated
- [ ] pip-audit and bandit run, findings fixed or documented
- [ ] .gitignore complete; git history searched for secrets

## Task 5 — Tests and quality
- [ ] Tests per core module (dataset, extraction, ranking, export, auth, ai_features mocked)
- [ ] Coverage >= 85 %; ruff clean
- [ ] Type hints and docstrings on public functions
- [ ] .pre-commit-config.yaml
- [ ] .github/workflows/ci.yml (3.10–3.12)

## Task 6 — Open-source files
- [ ] README.md (logo, all sections)
- [ ] README.md per folder
- [ ] docs/architecture.md with Mermaid
- [ ] LICENSE, SECURITY.md, CONTRIBUTING.md, CODE_OF_CONDUCT.md, CHANGELOG.md
- [ ] .env.example, requirements.txt, requirements-dev.txt, pyproject.toml
- [ ] Issue and PR templates
- [ ] Deployment notes and How to cite
- [ ] data/sample_resumes.csv (30–50 synthetic), Dockerfile non-root

## Task 7 — Features
- [ ] a. Skill aliases and boundary rules
- [ ] b. Better experience detection + include-unknown toggle
- [ ] c. Why this score (top 5 terms)
- [ ] d. Paste job description
- [ ] e. PDF/DOCX/TXT upload, short-file warning
- [ ] f. Blind screening
- [ ] g. scripts/evaluate.py
- [ ] h. Roles and saved shortlists
- [ ] i. Optional hybrid ranking

## Task 8 — Final verification
- [ ] pytest --cov, ruff, bandit, pip-audit, vulture
- [ ] Fresh venv start with sample data
- [ ] Report table

## Notes, assumptions and differences
- Python 3.12 and Git were not installed; installed with winget (user approved).
- The design images `docs/design/resume_search_ui_design.png` and
  `docs/design/resume_search_logo_in_app.png` do not exist anywhere on disk, so
  Task 3 follows the written spec only.
- `assets/` did not exist; only `C:\Parth\resume_search_icon.svg` was provided.
  The PNG assets are generated from that SVG (user approved).
