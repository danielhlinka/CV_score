from __future__ import annotations

import re


def extract_email(text: str) -> str | None:
    match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    return match.group(0) if match else None


def extract_phone(text: str) -> str | None:
    match = re.search(r"[\+]?\d[\d\s\-\.\(\)]{7,}\d", text)
    return match.group(0).strip() if match else None
