"""Reading and validating resume datasets.

There is one CSV reader (:func:`read_resume_csv`). It reads only the columns
the app needs, which keeps large uploads fast.
"""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd

from resume_search.config import (
    CATEGORY_COLUMN,
    DATASET_EXTENSIONS,
    MAX_UPLOAD_BYTES,
    MAX_UPLOAD_MB,
    NAME_COLUMN,
    RESUME_TEXT_COLUMNS,
)
from resume_search.text import has_words


def find_resume_column(df: pd.DataFrame) -> str:
    """Return the resume-text column present in ``df``.

    Raises:
        ValueError: when no supported column exists.
    """
    for column in RESUME_TEXT_COLUMNS:
        if column in df.columns:
            return column
    raise ValueError(
        "CSV is missing a supported resume-text column. Expected one of: "
        + ", ".join(RESUME_TEXT_COLUMNS)
    )


def is_resume_text_usable(series: pd.Series) -> bool:
    """Return True when at least one value in ``series`` contains words."""
    return any(has_words(value) for value in series.astype(str))


def validate_upload(filename: str, size: int, allowed_extensions: frozenset[str] = DATASET_EXTENSIONS) -> str:
    """Check an upload's extension and size *before* it is parsed.

    Returns:
        The lower-case extension, e.g. ``".csv"``.

    Raises:
        ValueError: for an unsupported type, an empty file or a file over the size limit.
    """
    extension = Path(filename or "").suffix.lower()
    if extension not in allowed_extensions:
        allowed = ", ".join(sorted(ext.lstrip(".").upper() for ext in allowed_extensions))
        raise ValueError(f"Unsupported file type. Upload one of: {allowed}.")
    if size <= 0:
        raise ValueError("Uploaded file is empty.")
    if size > MAX_UPLOAD_BYTES:
        raise ValueError(f"Uploaded file exceeds the maximum allowed size of {MAX_UPLOAD_MB} MB.")
    return extension


def read_resume_csv(file_bytes: bytes) -> pd.DataFrame:
    """Parse CSV bytes, keeping only the resume, category and name columns.

    Raises:
        ValueError: when the bytes are empty, too large or not a readable CSV.
    """
    if not file_bytes:
        raise ValueError("Uploaded file is empty.")
    if len(file_bytes) > MAX_UPLOAD_BYTES:
        raise ValueError(f"Uploaded file exceeds the maximum allowed size of {MAX_UPLOAD_MB} MB.")
    last_error: Exception | None = None
    for encoding in ("utf-8", "latin-1"):
        try:
            header = pd.read_csv(io.BytesIO(file_bytes), nrows=0, encoding=encoding)
            wanted = set(RESUME_TEXT_COLUMNS) | {CATEGORY_COLUMN, NAME_COLUMN}
            usecols = [column for column in header.columns if column in wanted] or None
            return pd.read_csv(
                io.BytesIO(file_bytes),
                dtype=str,
                usecols=usecols,
                encoding=encoding,
                on_bad_lines="skip",
            )
        except UnicodeDecodeError as error:
            last_error = error
        except Exception as error:  # pandas raises several parser error types
            raise ValueError(
                "Unable to read the uploaded CSV. It may be malformed or unsupported."
            ) from error
    raise ValueError(
        "Unable to read the uploaded CSV. It may be corrupted or use an unsupported encoding."
    ) from last_error


def validate_resume_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Check that ``df`` has rows and a usable resume-text column.

    Raises:
        ValueError: when the dataset cannot be searched.
    """
    if df.empty:
        raise ValueError("The CSV file contains no rows.")
    resume_column = find_resume_column(df)
    if not is_resume_text_usable(df[resume_column]):
        raise ValueError(
            "The CSV contains a resume-text column, but every resume value is blank "
            "or lacks usable text."
        )
    return df.reset_index(drop=True)


def load_resumes(file_bytes: bytes) -> pd.DataFrame:
    """Read and validate a resume CSV in one step."""
    return validate_resume_dataframe(read_resume_csv(file_bytes))
