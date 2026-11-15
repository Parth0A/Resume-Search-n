"""Tests for resume_search.dataset."""

from __future__ import annotations

import io

import pandas as pd
import pytest

from resume_search.config import MAX_UPLOAD_BYTES
from resume_search.dataset import (
    documents_to_dataframe,
    find_resume_column,
    is_resume_text_usable,
    load_resumes,
    read_document,
    read_resume_csv,
    validate_upload,
)


class TestLoadResumes:
    def test_loads_valid_csv(self):
        csv_content = "Resume_str,Category\nPython developer with 3 years of experience,Engineering\n"
        df = load_resumes(csv_content.encode("utf-8"))
        assert not df.empty
        assert "Resume_str" in df.columns

    def test_accepts_alternate_resume_column(self):
        df = load_resumes(b"Resume,Category\nBackend engineer resume\n")
        assert "Resume" in df.columns

    def test_accepts_category_column(self):
        df = load_resumes(b"Resume_str,Category\nResume text,Engineering\n")
        assert "Category" in df.columns

    def test_reads_only_needed_columns(self):
        df = read_resume_csv(b"Resume_str,Category,Name,Salary\ntext,Eng,Ann,100\n")
        assert set(df.columns) == {"Resume_str", "Category", "Name"}

    def test_reads_latin1(self):
        df = load_resumes("Resume_str\nCaf\xe9 manager resume\n".encode("latin-1"))
        assert df.iloc[0]["Resume_str"].startswith("Caf")

    def test_rejects_empty_file(self):
        with pytest.raises(ValueError):
            load_resumes(b"")

    def test_rejects_file_with_no_rows(self):
        with pytest.raises(ValueError):
            load_resumes(b"Resume_str,Category\n")

    def test_rejects_csv_without_resume_column(self):
        with pytest.raises(ValueError):
            load_resumes(b"Name,Email\nAlice,a@example.com\n")

    def test_rejects_csv_with_only_blank_resumes(self):
        with pytest.raises(ValueError):
            load_resumes(b"Resume_str,Category\n,\n,\n")

    def test_rejects_malformed_csv(self):
        with pytest.raises(ValueError):
            load_resumes(b"not a csv at all @@@@")


class TestValidateUpload:
    def test_accepts_csv(self):
        assert validate_upload("Resumes.CSV", 100) == ".csv"

    @pytest.mark.parametrize(("name", "size", "message"), [
        ("resumes.exe", 100, "Unsupported"),
        ("resumes", 100, "Unsupported"),
        ("resumes.csv", 0, "empty"),
        ("resumes.csv", MAX_UPLOAD_BYTES + 1, "maximum"),
    ])
    def test_rejects_bad_uploads(self, name, size, message):
        with pytest.raises(ValueError, match=message):
            validate_upload(name, size)

    def test_read_rejects_oversized_bytes(self, monkeypatch):
        monkeypatch.setattr("resume_search.dataset.MAX_UPLOAD_BYTES", 10)
        with pytest.raises(ValueError, match="maximum"):
            read_resume_csv(b"Resume_str\n" + b"x" * 20)


def _pdf(text: str) -> bytes:
    """Build a tiny one-page PDF containing ``text`` (synthetic, for tests only)."""
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode()
    objects = [
        b"<</Type/Catalog/Pages 2 0 R>>",
        b"<</Type/Pages/Kids[3 0 R]/Count 1>>",
        b"<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>",
        b"<</Length " + str(len(stream)).encode() + b">>stream\n" + stream + b"\nendstream",
        b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj".encode() + body + b"endobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    out += b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets)
    out += f"trailer<</Size {len(objects) + 1}/Root 1 0 R>>\nstartxref\n{xref}\n%%EOF".encode()
    return bytes(out)


def _docx(text: str) -> bytes:
    from docx import Document

    document = Document()
    document.add_paragraph(text)
    table = document.add_table(rows=1, cols=1)
    table.cell(0, 0).text = "Skills: Kubernetes"
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


LONG = " ".join(["Python developer with Django and SQL experience building APIs"] * 4)


class TestDocuments:
    def test_txt_utf8_and_latin1(self):
        assert read_document("Café manager".encode(), "a.txt") == "Café manager"
        assert read_document("Caf\xe9".encode("latin-1"), "b.TXT") == "Caf\xe9"

    def test_pdf(self):
        assert "Python developer" in read_document(_pdf("Python developer resume"), "cv.pdf")

    def test_docx_paragraphs_and_tables(self):
        text = read_document(_docx("Data analyst resume"), "cv.docx")
        assert "Data analyst resume" in text
        assert "Kubernetes" in text

    def test_damaged_pdf(self):
        with pytest.raises(ValueError, match="Could not read cv.pdf"):
            read_document(b"%PDF-1.4 garbage", "cv.pdf")

    def test_unsupported_type(self):
        with pytest.raises(ValueError, match="Unsupported"):
            read_document(b"data", "cv.csv")

    def test_documents_to_dataframe_with_short_file_warning(self):
        df, warnings = documents_to_dataframe([
            ("asha_rao.txt", LONG.encode()),
            ("short.pdf", _pdf("Python developer")),
        ])
        assert list(df["Name"]) == ["asha_rao", "short"]
        assert len(warnings) == 1 and "short.pdf has only" in warnings[0]

    def test_documents_to_dataframe_requires_files(self):
        with pytest.raises(ValueError, match="at least one"):
            documents_to_dataframe([])

    def test_documents_without_text_rejected(self):
        with pytest.raises(ValueError, match="blank"):
            documents_to_dataframe([("empty.txt", b"   ...   ")])

    def test_missing_library_message(self, monkeypatch):
        import builtins

        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "pypdf":
                raise ImportError("no pypdf")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        with pytest.raises(ValueError, match="pip install"):
            read_document(_pdf("x"), "cv.pdf")


class TestFindResumeColumn:
    def test_finds_preferred_column(self):
        df = pd.DataFrame({"Resume_str": ["text"], "Category": ["eng"]})
        assert find_resume_column(df) == "Resume_str"

    def test_finds_alternate_column(self):
        df = pd.DataFrame({"ResumeText": ["text"], "Category": ["eng"]})
        assert find_resume_column(df) == "ResumeText"

    def test_tries_ordered_alternatives(self):
        assert find_resume_column(pd.DataFrame({"Content": ["text"]})) == "Content"

    def test_raises_when_no_column_found(self):
        with pytest.raises(ValueError):
            find_resume_column(pd.DataFrame({"Name": ["Alice"]}))


class TestIsResumeTextUsable:
    def test_returns_true_for_usable_text(self):
        assert is_resume_text_usable(pd.Series(["", "  ", "Python engineer"])) is True

    def test_returns_false_for_blank_text(self):
        assert is_resume_text_usable(pd.Series(["", "  ", "!!!", "\t"])) is False

    def test_handles_non_string_values(self):
        assert is_resume_text_usable(pd.Series([None, 123, "useful text"])) is True
