from __future__ import annotations

import re
import unicodedata


def normalize_text(text: str) -> str:
    # هنا بننضف النص لأن جودة الـ embedding بتقل جدًا مع الضوضاء
    cleaned = text or ""
    cleaned = unicodedata.normalize("NFKC", cleaned)
    cleaned = re.sub(r"https?://\S+|www\.\S+", " ", cleaned)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    cleaned = re.sub(r"[^\w\s\-\+\.#]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip().lower()
    return cleaned


def compact_text(text: str, max_words: int = 280) -> str:
    words = normalize_text(text).split()
    if len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words])
