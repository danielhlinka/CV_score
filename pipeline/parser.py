from __future__ import annotations

from pipeline.contracts import ParsedCV
from pipeline.normalize.cv_normalizer import normalize_cv_text


def parse_cv(raw_text: str) -> ParsedCV:
    normalized = normalize_cv_text(raw_text)
    contact = normalized["contact"]

    return {
        "email": contact.get("email"),
        "phone": contact.get("phone"),
        "raw_text": raw_text,
        "raw_text_length": len(raw_text),
        "normalized": normalized,
    }
