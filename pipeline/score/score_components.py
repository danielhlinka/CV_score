from __future__ import annotations

from pipeline.lib.constants import EDUCATION_LEVEL_RANK, SENIORITY_LEVEL_RANK
from pipeline.lib.contracts import EnrichedCV, JobProfile
from pipeline.enrich.semantic_similarity import best_cosine_score, memoized_embedding


def skills_score(cv: EnrichedCV, job: JobProfile) -> float:
    """Score required-skill fit using exact and semantic matching signals.
    Applies confidence-aware fallback when extraction produced no skills."""
    if not job["skills"]:
        return 1.0
    cv_skills = [skill.lower() for skill in cv.get("skills", [])]
    confidence = cv.get("parser_confidence", "low")
    if not cv_skills:
        return 0.5 if confidence == "low" else 0.0
    matched = sum(1 for required_skill in job["skills"] if required_skill in cv_skills)
    exact = matched / len(job["skills"])

    if exact < 1.0:
        unmatched = [required_skill for required_skill in job["skills"] if required_skill not in cv_skills]
        cv_embeddings = [memoized_embedding(skill) for skill in cv_skills]

        per_skill_scores = []
        for req_skill in unmatched:
            req_emb = memoized_embedding(req_skill)
            best = best_cosine_score(req_emb, cv_embeddings)
            per_skill_scores.append(best)
        soft = sum(per_skill_scores) / len(per_skill_scores) if per_skill_scores else 0.0
        return round((exact + soft) / 2, 3)

    return round(exact, 3)


def seniority_score(cv: EnrichedCV, job: JobProfile) -> float:
    """Score level alignment between CV and job seniority expectations.
    Uses softer penalties when parser confidence is low."""
    cv_level = SENIORITY_LEVEL_RANK.get(cv.get("seniority", "junior"), 1)
    job_level = SENIORITY_LEVEL_RANK.get(job.get("seniority", "mid"), 2)
    diff = abs(cv_level - job_level)
    confidence = cv.get("parser_confidence", "low")
    if confidence == "low":
        return round(max(0.5, 1.0 - diff * 0.15), 3)
    if confidence == "medium":
        return round(max(0.35, 1.0 - diff * 0.2), 3)
    return round(max(0.0, 1.0 - diff * 0.25), 3)


def experience_score_component(cv: EnrichedCV, job: JobProfile) -> float:
    """Score years-of-experience sufficiency against job requirement.
    Applies confidence-based guardrails for missing parsed experience."""
    job_years = job.get("years_required", 0)
    if job_years == 0:
        return 1.0
    cv_years = float(cv.get("years_experience", 0) or 0)
    confidence = cv.get("parser_confidence", "low")
    if cv_years <= 0:
        if confidence == "low":
            return 0.45
        if confidence == "medium":
            return 0.25
        return 0.0
    ratio = cv_years / job_years
    return round(min(ratio, 1.0), 3)


def role_score(cv: EnrichedCV, job: JobProfile) -> float:
    """Score role-category compatibility between CV and job profile.
    Uses conservative defaults when either role signal is missing."""
    cv_role = cv.get("role_category", "").lower()
    job_role = job.get("role_category", "").lower()
    confidence = cv.get("parser_confidence", "low")
    if not cv_role or not job_role:
        return 0.5
    if confidence == "low":
        return 0.5 if cv_role != job_role else 0.8
    return 1.0 if cv_role == job_role else 0.2


def education_score(cv: EnrichedCV, job: JobProfile) -> float:
    """Score education-level coverage using configured rank ordering.
    Penalizes only the level gap when CV falls below requirement."""
    cv_level = EDUCATION_LEVEL_RANK.get(cv.get("education", "none"), 0)
    job_level = EDUCATION_LEVEL_RANK.get(job.get("education", "none"), 0)
    if cv_level >= job_level:
        return 1.0
    diff = job_level - cv_level
    return round(max(0.0, 1.0 - diff * 0.25), 3)
