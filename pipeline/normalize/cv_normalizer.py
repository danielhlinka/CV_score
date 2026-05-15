from __future__ import annotations

import re

from pipeline.lib.constants import ConfidenceLevel, ROLE_SIGNAL_KEYWORDS, SENIORITY_SIGNAL_KEYWORDS
from pipeline.lib.contracts import NormalizedCV
from pipeline.normalize.contact_parser import extract_email, extract_phone
from pipeline.normalize.education_parser import extract_education
from pipeline.normalize.experience_parser import parse_experience_entries
from pipeline.normalize.skills_parser import extract_skills


def _keyword_signals(text: str, mapping: dict[str, tuple[str, ...]]) -> dict[str, int]:
    """Count whole-word keyword hits for each taxonomy bucket.
    Produces deterministic signal counts used in role/seniority hints."""
    lowered = text.lower()
    signals: dict[str, int] = {}
    for key, keywords in mapping.items():
        count = 0
        for keyword in keywords:
            count += len(re.findall(rf"\b{re.escape(keyword.lower())}\b", lowered))
        signals[key] = count
    return signals


def _determine_parser_confidence(
    *,
    experience_confidence: ConfidenceLevel,
    skills_count: int,
    has_experience_entries: bool,
) -> ConfidenceLevel:
    """Derive overall parser confidence from extraction evidence quality.
    Downgrades confidence when supporting signals are sparse."""
    parser_confidence = experience_confidence
    if parser_confidence == "high" and skills_count < 2:
        parser_confidence = "medium"
    if parser_confidence == "medium" and not has_experience_entries:
        parser_confidence = "low"
    return parser_confidence


def _build_normalizer_warnings(
    *,
    experience_warnings: list[str],
    skills: list[str],
    education: str,
) -> list[str]:
    """Assemble user-facing warnings about weak extraction outcomes.
    Combines experience warnings with missing skills/education hints."""
    warnings = list(experience_warnings)
    if not skills:
        warnings.append("No skills detected from CV text.")
    if education == "none":
        warnings.append("No education level confidently detected.")
    return warnings


def normalize_cv_text(raw_text: str) -> NormalizedCV:
    """Normalize raw CV text into structured fields for scoring/enrichment.
    Aggregates contact, experience, skills, education, and confidence data."""
    experience_entries, experience_years, experience_conf, exp_warnings = parse_experience_entries(raw_text)

    skills = extract_skills(raw_text)
    education = extract_education(raw_text)

    role_signals = _keyword_signals(raw_text, ROLE_SIGNAL_KEYWORDS)
    seniority_signals = _keyword_signals(raw_text, SENIORITY_SIGNAL_KEYWORDS)

    strongest_role = max(role_signals, key=role_signals.get) if role_signals else "unknown"
    strongest_seniority_signal = max(seniority_signals, key=seniority_signals.get) if seniority_signals else "unknown"

    warnings = _build_normalizer_warnings(
        experience_warnings=exp_warnings,
        skills=skills,
        education=education,
    )
    parser_confidence = _determine_parser_confidence(
        experience_confidence=experience_conf,
        skills_count=len(skills),
        has_experience_entries=bool(experience_entries),
    )

    return {
        "contact": {
            "email": extract_email(raw_text),
            "phone": extract_phone(raw_text),
        },
        "experience_entries": experience_entries,
        "experience_years": experience_years,
        "experience_confidence": experience_conf,
        "skills": skills,
        "education": education,
        "role_signals": role_signals,
        "seniority_signals": seniority_signals,
        "strongest_role_signal": strongest_role,
        "strongest_seniority_signal": strongest_seniority_signal,
        "parser_confidence": parser_confidence,
        "warnings": warnings,
    }
