# Contributing to Resume Search

Thanks for helping! Please follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Set up

```bash
python -m venv .venv
# Windows: .\.venv\Scripts\activate    Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pre-commit install
```

## Rules of the codebase

- `resume_search/` must never import Streamlit. UI code in `ui/` calls only public functions
  (no leading underscore) of `resume_search`.
- Constants belong in `resume_search/config.py`; CSS belongs only in `ui/styles.css`.
- Any text from users or resumes that reaches `unsafe_allow_html` must go through the escaping
  helpers in `ui/components.py`.
- Never log e-mails, passwords or resume text. Never commit `.env`, databases or real resumes.

## Before opening a pull request

```bash
ruff check .
pytest -q --cov=resume_search          # keep coverage at or above 85 %
bandit -q -r resume_search ui app.py
vulture resume_search ui app.py --min-confidence 80
```

- Add or update tests for every behaviour change.
- Keep pull requests small and focused; describe *why* in the description.
- Update `CHANGELOG.md` under "Unreleased".
- Use synthetic data only in tests, screenshots and issues.
