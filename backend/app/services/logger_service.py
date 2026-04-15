from datetime import datetime


def build_log_message(step: str, message: str) -> str:
    timestamp = datetime.utcnow().strftime("%H:%M:%S")
    return f"[{timestamp}] {step}: {message}"
