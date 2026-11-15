"""All constants used by Resume Search, in one place."""

from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "Resume Search"
APP_VERSION = "1.0"

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Datasets
# ---------------------------------------------------------------------------
RESUME_TEXT_COLUMNS: tuple[str, ...] = ("Resume_str", "Resume", "ResumeText", "Text", "Content")
"""Accepted resume-text column names, in order of preference."""

CATEGORY_COLUMN = "Category"
NAME_COLUMN = "Name"
"""Optional columns read from a CSV when present."""

MAX_UPLOAD_MB = 200
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024

DATASET_EXTENSIONS: frozenset[str] = frozenset({".csv"})
DOCUMENT_EXTENSIONS: frozenset[str] = frozenset({".pdf", ".docx", ".txt"})

MIN_RESUME_WORDS = 30
"""Single resumes shorter than this produce a warning."""

# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------
DEFAULT_RESULTS_LIMIT = 10
RESULT_LIMIT_OPTIONS: tuple[int, ...] = (5, 10, 25, 50)
TOP_TERMS = 5
"""Number of terms shown in "Why this score"."""

EXPERIENCE_OPTIONS: tuple[str, ...] = (
    "Any experience", "1 year", "2 years", "3 years", "5 years", "7 years", "10 years",
)

JOB_ROLES: tuple[str, ...] = (
    "Software Engineer", "Python Developer", "Java Developer", "Frontend Developer",
    "Backend Developer", "Full Stack Developer", "Data Analyst", "Data Scientist",
    "Machine Learning Engineer", "AI Engineer", "DevOps Engineer", "Cybersecurity Analyst",
    "Web Developer", "Mobile App Developer", "UI / UX Designer", "QA / Test Engineer",
)

SKILL_OPTIONS: tuple[str, ...] = (
    "Python", "Java", "JavaScript", "TypeScript", "C", "C++", "C#", "HTML", "CSS", "React",
    "Angular", "Node.js", "Django", "Flask", "SQL", "MySQL", "PostgreSQL", "MongoDB", "Excel",
    "Power BI", "Pandas", "NumPy", "Machine Learning", "Deep Learning", "AI", "TensorFlow",
    "PyTorch", "Git", "GitHub", "Docker", "AWS", "Azure", "Linux", "Cybersecurity",
    "Networking", "REST API", "Figma", "UI/UX", "Selenium", "Testing", "Communication",
)

SKILL_ALIASES: dict[str, tuple[str, ...]] = {
    "node.js": ("node.js", "nodejs", "node js"),
    "machine learning": ("machine learning", "ml"),
    "javascript": ("javascript", "js"),
    "postgresql": ("postgresql", "postgres"),
    "typescript": ("typescript", "ts"),
    "artificial intelligence": ("artificial intelligence", "ai"),
    "ai": ("ai", "artificial intelligence"),
    "rest api": ("rest api", "rest apis", "restful api", "restful apis"),
    "c#": ("c#", "csharp"),
    "c++": ("c++", "cpp"),
}
"""Canonical (lower-case) skill -> spellings that count as the same skill."""

HYBRID_MODEL_NAME = "all-MiniLM-L6-v2"
HYBRID_TFIDF_WEIGHT = 0.5
SEARCH_METHODS: tuple[str, ...] = ("tfidf", "hybrid")

# ---------------------------------------------------------------------------
# Accounts and security
# ---------------------------------------------------------------------------
ROLE_RECRUITER = "Recruiter"
ROLE_JOB_SEEKER = "Job seeker"
ROLES: tuple[str, ...] = (ROLE_RECRUITER, ROLE_JOB_SEEKER)

PBKDF2_ITERATIONS = 600_000
MIN_PASSWORD_LENGTH = 8
MAX_FAILED_LOGINS = 5
LOCKOUT_MINUTES = 15
SESSION_TIMEOUT_MINUTES = 30

DB_PATH = Path(os.getenv("RESUME_SEARCH_DB", str(PROJECT_ROOT / "resume_search.db")))
"""SQLite database file; override with the RESUME_SEARCH_DB environment variable."""

COMMON_PASSWORDS: frozenset[str] = frozenset({
    "password", "password1", "password123", "passw0rd", "12345678", "123456789",
    "1234567890", "qwerty123", "qwertyuiop", "iloveyou", "11111111", "00000000",
    "abc12345", "abcd1234", "letmein1", "welcome1", "welcome123", "admin123",
    "football", "baseball", "sunshine", "princess", "trustno1", "superman",
    "starwars", "dragon123", "monkey123", "123123123", "1q2w3e4r", "zaq12wsx",
    "changeme", "resumesearch",
})

# ---------------------------------------------------------------------------
# Gemini
# ---------------------------------------------------------------------------
GEMINI_DEFAULT_MODEL = "gemini-2.5-flash"
MAX_RESUME_CHARS = 12_000
MAX_JOB_DESCRIPTION_CHARS = 8_000
