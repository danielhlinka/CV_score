from __future__ import annotations

import re

from pipeline.input.cv_text_extractor import SUPPORTED_EXTENSIONS, extract_text
from pipeline.normalize.education_parser import extract_education
from pipeline.normalize.skills_parser import extract_skills


def validate_text(text: str, min_chars: int = 200) -> bool:
    return len(text.strip()) >= min_chars


SECTION_HEADERS = {
    "work": r"work experience|experience|employment|pracovné skúsenosti|zamestnanie",
    "skills": r"skills|technical skills|zručnosti|znalosti",
    "education": r"education|vzdelanie|qualifications",
}


def extract_sections(text: str) -> dict:
    sections = {"work": "", "skills": "", "education": "", "other": ""}
    header_pattern = r"(" + "|".join(SECTION_HEADERS.values()) + r")"
    splits = re.split(header_pattern, text, flags=re.IGNORECASE)

    current = "other"
    for chunk in splits:
        matched = False
        for section, pattern in SECTION_HEADERS.items():
            if re.fullmatch(pattern, chunk.strip(), re.IGNORECASE):
                current = section
                matched = True
                break
        if not matched:
            sections[current] += chunk

    return sections
