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
    DOCUMENT_EXTENSIONS,
    MAX_UPLOAD_BYTES,
    MAX_UPLOAD_MB,
    MIN_RESUME_WORDS,
    NAME_COLUMN,
    RESUME_TEXT_COLUMNS,
)
from resume_search.text import has_words, word_count


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


def read_document(file_bytes: bytes, filename: str) -> str:
    """Extract plain text from one PDF, DOCX or TXT resume.

    Raises:
        ValueError: when the file type is unsupported or the file cannot be read.
    """
    extension = validate_upload(filename, len(file_bytes), DOCUMENT_EXTENSIONS)
    try:
        if extension == ".txt":
            try:
                return file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                return file_bytes.decode("latin-1")
        if extension == ".pdf":
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(file_bytes))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        from docx import Document

        document = Document(io.BytesIO(file_bytes))
        parts = [paragraph.text for paragraph in document.paragraphs]
        for table in document.tables:
            parts.extend(cell.text for row in table.rows for cell in row.cells)
        return "\n".join(parts)
    except ImportError as error:
        raise ValueError(
            "PDF and DOCX support needs the 'pypdf' and 'python-docx' packages (pip install -r requirements.txt)."
        ) from error
    except Exception as error:  # parsers raise many different error types for damaged files
        raise ValueError(f"Could not read {Path(filename).name}. The file may be damaged or protected.") from error


def documents_to_dataframe(files: list[tuple[str, bytes]]) -> tuple[pd.DataFrame, list[str]]:
    """Turn individual resume files into a dataset (one row per file).

    Returns:
        The validated dataframe (``Name`` = file name without extension) and a list of
        warnings for files with fewer than ``MIN_RESUME_WORDS`` words.

    Raises:
        ValueError: when no file is given, a file cannot be read or nothing has text.
    """
    if not files:
        raise ValueError("Upload at least one resume file.")
    names: list[str] = []
    texts: list[str] = []
    warnings: list[str] = []
    for filename, file_bytes in files:
        text = read_document(file_bytes, filename)
        words = word_count(text)
        if words < MIN_RESUME_WORDS:
            warnings.append(
                f"{Path(filename).name} has only {words} words — it may be a scan or mostly images, "
                "so its score may be unreliable."
            )
        names.append(Path(filename).stem)
        texts.append(text)
    df = pd.DataFrame({NAME_COLUMN: names, CATEGORY_COLUMN: [""] * len(texts), RESUME_TEXT_COLUMNS[0]: texts})
    return validate_resume_dataframe(df), warnings
