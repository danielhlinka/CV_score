import re
from typing import Optional

def _extract_email(text: str) -> Optional[str]:
    match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    return match.group(0) if match else None


def _extract_phone(text: str) -> Optional[str]:
    match = re.search(r'[\+]?[\d][\d\s\-\.\(\)]{7,}[\d]', text)
    return match.group(0).strip() if match else None


def parse_cv(raw_text: str) -> dict:

    return {
        "email":                     _extract_email(raw_text),
        "phone":                     _extract_phone(raw_text),
        "raw_text":                  raw_text,
        "raw_text_length":           len(raw_text),
    }