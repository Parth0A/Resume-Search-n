# Security policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | Yes       |

## Reporting a vulnerability

Please **do not** open a public issue for security problems. Use GitHub's
*Security → Report a vulnerability* (private advisory) on this repository, or contact a maintainer
privately. Include steps to reproduce, the affected version and the impact. Expect an
acknowledgement within 7 days.

## What is in scope

- Authentication and lockout bypass, password hash weaknesses
- Cross-user data access (shortlists)
- HTML or Markdown injection through uploaded resumes
- CSV formula injection in exports
- Leaks of resume text, e-mails or API keys in logs or to third parties

## Operator checklist

- Keep `GEMINI_API_KEY` in `.env` or Streamlit secrets; never commit it.
- Store the SQLite database (`RESUME_SEARCH_DB`) somewhere only the app user can read.
- Run behind HTTPS when exposed beyond `localhost`.
- Only upload resumes you have permission to process.

The latest internal review is in [SECURITY_REVIEW.md](SECURITY_REVIEW.md).
