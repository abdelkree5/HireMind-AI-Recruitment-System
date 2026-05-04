from __future__ import annotations

from io import BytesIO
from pathlib import Path
import re
import unicodedata
from zipfile import BadZipFile, ZipFile
from xml.etree import ElementTree

SUPPORTED_EXTENSIONS = {".pdf", ".docx"}

class ResumeParser:
    """Unified parser for extracting text from PDF and DOCX resumes."""
    
    def parse(self, file_bytes: bytes, filename: str) -> str:
        suffix = Path(filename).suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            raise ValueError("الملف لازم يكون PDF أو DOCX")

        if suffix == ".pdf":
            raw_text = self._extract_pdf_text(file_bytes)
        else:
            raw_text = self._extract_docx_text(file_bytes)

        cleaned_text = self._clean_extracted_text(raw_text)
        self._validate_extracted_text(cleaned_text, filename)
        return cleaned_text

    def _extract_pdf_text(self, file_bytes: bytes) -> str:
        errors: list[str] = []
        try:
            import fitz
            with fitz.open(stream=file_bytes, filetype="pdf") as document:
                pages = [page.get_text("text") or "" for page in document]
            text = "\n".join(part for part in pages if part.strip()).strip()
            if text: return text
            errors.append("PyMuPDF extracted empty text")
        except (ModuleNotFoundError, Exception) as exc:
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
            if text: return text
            errors.append("pdfplumber extracted empty text")
        except (ModuleNotFoundError, Exception) as exc:
            errors.append(f"pdfplumber failed: {exc}")

        details = "; ".join(errors) if errors else "unknown parsing error"
        raise ValueError(f"Unable to extract readable text from PDF. {details}")

    def _extract_docx_text(self, file_bytes: bytes) -> str:
        try:
            from docx import Document
            document = Document(BytesIO(file_bytes))
            paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
            text = "\n".join(paragraphs).strip()
            if text: return text
            return self._extract_docx_text_from_zip(file_bytes)
        except Exception:
            return self._extract_docx_text_from_zip(file_bytes)

    def _extract_docx_text_from_zip(self, file_bytes: bytes) -> str:
        try:
            with ZipFile(BytesIO(file_bytes)) as archive:
                document_xml = archive.read("word/document.xml")
        except Exception:
            raise ValueError("Unable to parse DOCX content")

        root = ElementTree.fromstring(document_xml)
        namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        paragraphs: list[str] = []
        for paragraph in root.findall(".//w:p", namespace):
            texts = [node.text for node in paragraph.findall(".//w:t", namespace) if node.text]
            line = "".join(texts).strip()
            if line: paragraphs.append(line)

        if paragraphs: return "\n".join(paragraphs).strip()
        raise ValueError("Unable to extract readable text from DOCX")

    def _clean_extracted_text(self, text: str) -> str:
        normalized = unicodedata.normalize("NFKC", text or "")
        normalized = normalized.replace("\x00", " ").replace("", " ")
        cleaned_lines: list[str] = []
        for line in normalized.splitlines():
            if re.match(r"^\s*(%PDF-|PK\x03\x04|xref|endobj|obj\b|stream\b)", line, flags=re.IGNORECASE):
                continue
            visible = "".join(ch for ch in line if ch.isprintable() or ch in "\t ")
            visible = re.sub(r"\s+", " ", visible).strip()
            if visible: cleaned_lines.append(visible)
        return "\n".join(cleaned_lines).strip()

    def _validate_extracted_text(self, text: str, filename: str) -> None:
        length = len(text)
        alpha_count = sum(1 for ch in text if ch.isalpha())
        if length < 80 or alpha_count < 30:
            raise ValueError(f"Extracted CV text is not readable enough. File: {filename}")
