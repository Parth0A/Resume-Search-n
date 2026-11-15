## What and why

## How it was tested

- [ ] `pytest -q --cov=resume_search` passes (coverage ≥ 85 %)
- [ ] `ruff check .` is clean
- [ ] `bandit -q -r resume_search ui app.py` is clean
- [ ] UI changes checked in the browser (screenshots below, synthetic data only)

## Checklist

- [ ] `resume_search/` still has no Streamlit import
- [ ] User or resume text shown with `unsafe_allow_html` goes through `ui/components.py` escaping
- [ ] No secrets, databases or real resumes committed
- [ ] `CHANGELOG.md` updated
