from __future__ import annotations

from pipeline.lib.contracts import ParsedCV
from pipeline.normalize.cv_normalizer import normalize_cv_text


def parse_cv(raw_text: str) -> ParsedCV:
    """Convert raw CV text into the parsed contract used downstream.
    Includes normalized signals plus backward-compatible top-level fields."""
    normalized = normalize_cv_text(raw_text)
    contact = normalized["contact"]

    return {
        "email": contact.get("email"),
        "phone": contact.get("phone"),
        "raw_text": raw_text,
        "raw_text_length": len(raw_text),
        "normalized": normalized,
    }
