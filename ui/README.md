# ui — Streamlit screens

Calls only public functions of `resume_search`. All styling lives in `styles.css`.

| File | What it does |
|------|--------------|
| `styles.css` | The single stylesheet: design tokens, components, screens, responsive rules. |
| `theme.py` | Injects `styles.css` into the page. |
| `components.py` | HTML helpers (icon, brand, chips, bars, avatar, card header, KPI tiles, empty state). Escapes all text. |
| `state.py` | Session-state keys, sign-in/out, navigation, session timeout, step tracker status. |
| `auth_view.py` | Sign-in / create-account page. |
| `sidebar.py` | Navy sidebar with navigation and the profile card. |
| `header.py` | Header bar with page title, step tracker and user. |
| `upload_view.py` | Card 1: upload, validate and index a dataset (with timed status steps). |
| `search_view.py` | Card 2: role, skills, job description, toggles, search. |
| `results_view.py` | Card 3: KPIs, ranked table, candidate panel, profiles, charts, export, shortlist, AI summary. |
| `seeker_view.py` | Job-seeker page: check your own resume against a job description. |
| `ai_view.py` | Gemini tools page and the secrets-based API-key lookup. |
| `profile_view.py` | My profile, Privacy and data (Clear my data) and Saved shortlists pages. |
