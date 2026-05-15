from __future__ import annotations


def extract_education(text: str) -> str:
    """Infer highest education level from keyword evidence in CV text.
    Returns a normalized level label consumed by scoring rules."""
    text_lower = text.lower()

    if any(keyword in text_lower for keyword in ["phd", "ph.d", "doc.", "prof.", "doctorate"]):
        return "phd"
    if any(keyword in text_lower for keyword in ["master", "msc", "m.sc", "ing.", "mgr.", "mba"]):
        return "master"
    if any(keyword in text_lower for keyword in ["university", "univerzita", "bachelor", "bsc", "b.sc", "utb"]):
        return "bachelor"
    if any(
        keyword in text_lower
        for keyword in ["secondary", "high school", "spše", "stredná", "gymnázium", "spse", "stredna", "gymnazium"]
    ):
        return "high_school"

    return "none"
