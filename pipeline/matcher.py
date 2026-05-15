from pipeline import (
    EDUCATION_LEVEL_RANK,
    EnrichedCV,
    JobProfile,
    MatchResult,
    ScoreBreakdown,
    SENIORITY_LEVEL_RANK,
)
from pipeline.semantic import best_cosine_score, memoized_embedding

WEIGHTS = {
    "skills":     0.40,
    "seniority":  0.25,
    "experience": 0.25,
    "role":       0.05,
    "education":  0.05,
}


def _skills_score(cv: EnrichedCV, job: JobProfile) -> float:
    """Legacy skills component scorer kept for import compatibility.
    Blends exact skill hits with semantic fallback similarity."""
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


def _seniority_score(cv: EnrichedCV, job: JobProfile) -> float:
    """Legacy seniority scorer with parser-confidence-aware penalties.
    Retained to preserve historical behavior and tests."""
    cv_level = SENIORITY_LEVEL_RANK.get(cv.get("seniority", "junior"), 1)
    job_level = SENIORITY_LEVEL_RANK.get(job.get("seniority", "mid"), 2)
    diff = abs(cv_level - job_level)
    confidence = cv.get("parser_confidence", "low")
    if confidence == "low":
        return round(max(0.5, 1.0 - diff * 0.15), 3)
    if confidence == "medium":
        return round(max(0.35, 1.0 - diff * 0.2), 3)
    return round(max(0.0, 1.0 - diff * 0.25), 3)


def _experience_score(cv: EnrichedCV, job: JobProfile) -> float:
    """Legacy experience-years scorer for backward-compatible imports.
    Keeps conservative fallbacks when parsed years are missing."""
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


def _role_score(cv: EnrichedCV, job: JobProfile) -> float:
    """Legacy role-category alignment scorer.
    Uses confidence-based defaults for uncertain parser output."""
    cv_role  = cv.get("role_category", "").lower()
    job_role = job.get("role_category", "").lower()
    confidence = cv.get("parser_confidence", "low")
    if not cv_role or not job_role:
        return 0.5
    if confidence == "low":
        return 0.5 if cv_role != job_role else 0.8
    return 1.0 if cv_role == job_role else 0.2


def _education_score(cv: EnrichedCV, job: JobProfile) -> float:
    """Legacy education scorer based on ranked education levels.
    Penalizes only the gap below required education threshold."""
    cv_level = EDUCATION_LEVEL_RANK.get(cv.get("education", "none"), 0)
    job_level = EDUCATION_LEVEL_RANK.get(job.get("education", "none"), 0)
    if cv_level >= job_level:
        return 1.0
    diff = job_level - cv_level
    return round(max(0.0, 1.0 - diff * 0.25), 3)


def match(cv: EnrichedCV, job: JobProfile) -> MatchResult:
    """Legacy match aggregator kept stable for existing call sites.
    Computes weighted final score and attaches parser metadata."""
    scores: ScoreBreakdown = {
        "skills":     _skills_score(cv, job),
        "seniority":  _seniority_score(cv, job),
        "experience": _experience_score(cv, job),
        "role":       _role_score(cv, job),
        "education":  _education_score(cv, job),
    }

    final = sum(scores[k] * WEIGHTS[k] for k in scores)

    return {
        "final_score": round(final, 3),
        "breakdown":   scores,
        "parser_confidence": cv.get("parser_confidence", "low"),
        "parser_warnings": cv.get("parser_warnings", []),
        "cv":          cv,
        "job":         job,
    }
