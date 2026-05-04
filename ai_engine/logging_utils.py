from __future__ import annotations
from datetime import datetime

def build_log_message(step: str, message: str) -> str:
    timestamp = datetime.utcnow().strftime("%H:%M:%S")
    return f"[{timestamp}] {step}: {message}"

def arabic_log(step: str, detail: str) -> str:
    return build_log_message(step, detail)
