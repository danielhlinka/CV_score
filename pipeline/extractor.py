from __future__ import annotations

"""Backward-compatible extraction exports used by web handlers and tests."""

from pipeline.input.cv_text_extractor import SUPPORTED_EXTENSIONS, extract_text
from pipeline.normalize.education_parser import extract_education
from pipeline.normalize.skills_parser import extract_skills

__all__ = [
    "SUPPORTED_EXTENSIONS",
    "extract_education",
    "extract_skills",
    "extract_text",
]
