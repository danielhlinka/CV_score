from __future__ import annotations

from typing import NotRequired, TypedDict

from pipeline.constants import ConfidenceLevel, EducationLevel, JobRoleCategory, SeniorityLevel


class ContactInfo(TypedDict):
    email: str | None
    phone: str | None


class ExperienceEntry(TypedDict):
    title: str
    start_year: int
    end_year: int
    years: float
    range_text: str


class NormalizedCV(TypedDict):
    contact: ContactInfo
    experience_entries: list[ExperienceEntry]
    experience_years: float
    experience_confidence: ConfidenceLevel
    skills: list[str]
    education: EducationLevel
    role_signals: dict[str, int]
    seniority_signals: dict[str, int]
    strongest_role_signal: str
    strongest_seniority_signal: str
    parser_confidence: ConfidenceLevel
    warnings: list[str]


class ParsedCV(TypedDict):
    email: str | None
    phone: str | None
    raw_text: str
    raw_text_length: int
    normalized: NormalizedCV


class EnrichedCV(ParsedCV):
    role_category: str
    role_category_secondary: str
    role_scores: dict[str, float]
    seniority: SeniorityLevel
    seniority_scores: dict[str, float]
    seniority_combined: dict[str, float]
    jobs: list[ExperienceEntry]
    total_exp_score: float
    years_experience: float
    skills: list[str]
    education: EducationLevel
    parser_confidence: ConfidenceLevel
    parser_warnings: list[str]


class JobProfile(TypedDict):
    job_title: str
    seniority: SeniorityLevel
    years_required: int
    skills: list[str]
    education: EducationLevel
    role_category: JobRoleCategory


class ScoreBreakdown(TypedDict):
    skills: float
    seniority: float
    experience: float
    role: float
    education: float


class MatchResult(TypedDict):
    final_score: float
    breakdown: ScoreBreakdown
    parser_confidence: ConfidenceLevel
    parser_warnings: list[str]
    cv: EnrichedCV
    job: JobProfile
    explanation: NotRequired[str]
