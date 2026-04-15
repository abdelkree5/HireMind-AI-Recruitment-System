from __future__ import annotations

from backend.app.services.document_parser import extract_text_from_resume


class ResumeParser:
    def parse(self, file_bytes: bytes, filename: str) -> str:
        return extract_text_from_resume(file_bytes, filename)
