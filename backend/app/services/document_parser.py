from __future__ import annotations

from io import BytesIO
from pathlib import Path
import re
import unicodedata
from zipfile import BadZipFile, ZipFile
from xml.etree import ElementTree



SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


def extract_text_from_resume(file_bytes: bytes, filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError("الملف لازم يكون PDF أو DOCX")

    if suffix == ".pdf":
        raw_text = _extract_pdf_text(file_bytes)
    else:
        raw_text = _extract_docx_text(file_bytes)

    cleaned_text = _clean_extracted_text(raw_text)
    _validate_extracted_text(cleaned_text, filename)
    return cleaned_text


def _extract_pdf_text(file_bytes: bytes) -> str:
    errors: list[str] = []

    try:
        import fitz

        with fitz.open(stream=file_bytes, filetype="pdf") as document:
            pages = [page.get_text("text") or "" for page in document]
        text = "\n".join(part for part in pages if part.strip()).strip()
        if text:
            return text
        errors.append("PyMuPDF extracted empty text")
    except ModuleNotFoundError:
        errors.append("PyMuPDF (fitz) is not installed")
    except Exception as exc:  # pragma: no cover - parser-specific errors
        errors.append(f"PyMuPDF failed: {exc}")

    try:
        import pdfplumber

        text_parts: list[str] = []
        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                if page_text.strip():
                    text_parts.append(page_text)
        text = "\n".join(text_parts).strip()
        if text:
            return text
        errors.append("pdfplumber extracted empty text")
    except ModuleNotFoundError:
        errors.append("pdfplumber is not installed")
    except Exception as exc:  # pragma: no cover - parser-specific errors
        errors.append(f"pdfplumber failed: {exc}")

    details = "; ".join(errors) if errors else "unknown parsing error"
    raise ValueError(f"Unable to extract readable text from PDF. {details}")


def _extract_docx_text(file_bytes: bytes) -> str:
    try:
        from docx import Document

        document = Document(BytesIO(file_bytes))
        paragraphs = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
        text = "\n".join(paragraphs).strip()
        if text:
            return text
        return _extract_docx_text_from_zip(file_bytes)
    except ModuleNotFoundError:
        return _extract_docx_text_from_zip(file_bytes)
    except Exception:
        # Fallback to XML extraction for partially malformed DOCX files.
        return _extract_docx_text_from_zip(file_bytes)


def _extract_docx_text_from_zip(file_bytes: bytes) -> str:
    try:
        with ZipFile(BytesIO(file_bytes)) as archive:
            document_xml = archive.read("word/document.xml")
    except (BadZipFile, KeyError, OSError):
        raise ValueError("Unable to parse DOCX content")

    try:
        root = ElementTree.fromstring(document_xml)
    except ElementTree.ParseError:
        raise ValueError("Unable to parse DOCX XML content")

    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs: list[str] = []
    for paragraph in root.findall(".//w:p", namespace):
        texts = [node.text for node in paragraph.findall(".//w:t", namespace) if node.text]
        line = "".join(texts).strip()
        if line:
            paragraphs.append(line)

    if paragraphs:
        return "\n".join(paragraphs).strip()

    raise ValueError("Unable to extract readable text from DOCX")


def _clean_extracted_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text or "")
    normalized = normalized.replace("\x00", " ")
    normalized = normalized.replace("�", " ")

    cleaned_lines: list[str] = []
    for line in normalized.splitlines():
        # Strip known binary/container markers that may leak from malformed extraction.
        if re.match(r"^\s*(%PDF-|PK\x03\x04|xref|endobj|obj\b|stream\b)", line, flags=re.IGNORECASE):
            continue

        visible = "".join(ch for ch in line if ch.isprintable() or ch in "\t ")
        visible = re.sub(r"\s+", " ", visible).strip()
        if visible:
            cleaned_lines.append(visible)

    cleaned = "\n".join(cleaned_lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _validate_extracted_text(text: str, filename: str) -> None:
    preview = text[:1000]
    length = len(text)
    alpha_count = sum(1 for ch in text if ch.isalpha())
    printable_count = sum(1 for ch in text if ch.isprintable() or ch in "\n\t")
    printable_ratio = (printable_count / length) if length else 0.0
    binary_markers = len(re.findall(r"(%PDF-|PK\x03\x04|xref|endobj|/Type|stream)", text, flags=re.IGNORECASE))

    looks_unreadable = (
        length < 80
        or alpha_count < 30
        or printable_ratio < 0.9
        or binary_markers > 12
    )

    if looks_unreadable:
        raise ValueError(
            "Extracted CV text is not readable enough for analysis. "
            f"File: {filename}. Preview: {preview}"
        )
