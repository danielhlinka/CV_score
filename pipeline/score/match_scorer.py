from __future__ import annotations

from pipeline.contracts import EnrichedCV, JobProfile, MatchResult, ScoreBreakdown
from pipeline.score.score_components import (
    education_score,
    experience_score_component,
    role_score,
    seniority_score,
    skills_score,
)
from pipeline.score.score_weights import WEIGHTS


def match(cv: EnrichedCV, job: JobProfile) -> MatchResult:
    """Combine weighted score components into a final match result.
    Preserves parser confidence metadata for downstream consumers."""
    scores: ScoreBreakdown = {
        "skills": skills_score(cv, job),
        "seniority": seniority_score(cv, job),
        "experience": experience_score_component(cv, job),
        "role": role_score(cv, job),
        "education": education_score(cv, job),
    }

    final = sum(scores[key] * WEIGHTS[key] for key in scores)

    return {
        "final_score": round(final, 3),
        "breakdown": scores,
        "parser_confidence": cv.get("parser_confidence", "low"),
        "parser_warnings": cv.get("parser_warnings", []),
        "cv": cv,
        "job": job,
    }
