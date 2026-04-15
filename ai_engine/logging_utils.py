from __future__ import annotations

from datetime import datetime


def arabic_log(step: str, detail: str) -> str:
    return f"[{datetime.utcnow().strftime('%H:%M:%S')}] {step} - {detail}"
