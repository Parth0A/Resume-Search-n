# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses semantic versioning.

## [Unreleased]

## [1.0.0] - 2026-11-15

### Fixed
- Mixed-case resumes scored 0 because the query was lower-cased but the resumes were not. Queries
  and resumes now share one normalisation.

### Added
- New UI: two-column sign-in page, navy sidebar with navigation, header with step tracker,
  upload / role / results cards, KPI tiles, candidate panel, Profiles and Charts tabs, Saved
  shortlists, AI tools, My profile, and Privacy and data pages.
- Branding: logo, icon and favicon.
- "Why this score" term contributions; job-description ranking; blind screening; include-unknown
  experience toggle; skill aliases; better experience detection; PDF/DOCX/TXT uploads; saved
  shortlists; job-seeker resume check; optional hybrid ranking; `scripts/evaluate.py`.
- Security: PBKDF2 600,000 iterations with per-user iteration counts and re-hashing, lockout after
  5 failures, 30-minute session timeout, password rules, upload validation, CSV formula-injection
  protection, Gemini reply validation.
- Tests for every core module, CI workflow, pre-commit, Dockerfile, documentation.

### Changed
- Code split into the `resume_search` core package and the `ui` Streamlit package.
- Upload limit lowered from 1 GB to 200 MB.
