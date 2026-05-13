from pipeline.normalizer import normalize_cv_text
from pipeline import ParsedCV


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
