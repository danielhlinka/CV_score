from __future__ import annotations

from functools import cache

from pipeline.lib.constants import ROLE_TEMPLATES, SENIORITY_TEMPLATES
from pipeline.lib.contracts import EnrichedCV, ParsedCV
from pipeline.enrich.seniority_model import combined_seniority, experience_score
from pipeline.enrich.semantic_similarity import Embedding, memoized_embedding, template_scores


@cache
def _get_role_template_embeddings() -> dict[str, Embedding]:
    """Compute and cache embeddings for each role template sentence.
    Avoids repeated embedding calls across CV enrich operations."""
    return {role: memoized_embedding(template) for role, template in ROLE_TEMPLATES.items()}


@cache
def _get_seniority_template_embeddings() -> dict[str, Embedding]:
    """Compute and cache embeddings for seniority template sentences.
    Shared cache improves determinism and runtime efficiency."""
    return {level: memoized_embedding(template) for level, template in SENIORITY_TEMPLATES.items()}


def _normalized_signal_scores(signals: dict[str, int]) -> dict[str, float]:
    """Normalize integer keyword-signal counts into `[0, 1]` scores.
    Preserves key set and handles empty/non-positive inputs safely."""
    if not signals:
        return {}
    max_value = max(signals.values())
    if max_value <= 0:
        return {k: 0.0 for k in signals}
    return {k: float(v) / float(max_value) for k, v in signals.items()}


def enrich_cv(parsed: ParsedCV) -> EnrichedCV:
    """Enrich parsed CV with semantic role/seniority and scoring helpers.
    Combines normalized signals, template similarity, and experience data."""
    normalized = parsed["normalized"]
    skills = normalized.get("skills", [])
    jobs = normalized.get("experience_entries", [])
    years = float(normalized.get("experience_years", 0.0))

    role_signals = normalized.get("role_signals", {})
    role_signal_scores = _normalized_signal_scores(role_signals)

    seniority_signals = normalized.get("seniority_signals", {})
    seniority_signal_scores = _normalized_signal_scores(seniority_signals)

    role_hint = normalized.get("strongest_role_signal", "")
    titles_text = " ".join(job.get("title", "") for job in jobs if job.get("title") and job.get("title") != "unknown")

    semantic_profile = " ".join(part for part in [" ".join(skills), titles_text, role_hint] if part)
    cv_emb = memoized_embedding(semantic_profile)

    role_template_embeddings = _get_role_template_embeddings()
    role_semantic_scores = template_scores(cv_emb, role_template_embeddings)

    role_scores = {}
    for role in role_semantic_scores:
        semantic = role_semantic_scores.get(role, 0.0)
        signal = role_signal_scores.get(role, 0.0)
        role_scores[role] = round((semantic * 0.7) + (signal * 0.3), 4)

    seniority_profile = " ".join(
        part
        for part in [
            titles_text,
            " ".join(skills[:20]),
            normalized.get("strongest_seniority_signal", ""),
            f"{years:.2f} years experience",
        ]
        if part
    )
    seniority_emb = memoized_embedding(seniority_profile)

    seniority_template_embeddings = _get_seniority_template_embeddings()
    sem_seniority_scores = template_scores(seniority_emb, seniority_template_embeddings)

    seniority_scores = {}
    for level in sem_seniority_scores:
        semantic = sem_seniority_scores.get(level, 0.0)
        signal = seniority_signal_scores.get(level, 0.0)
        seniority_scores[level] = round((semantic * 0.75) + (signal * 0.25), 4)

    seniority, seniority_combined = combined_seniority(seniority_scores, int(round(years)))

    top_roles = sorted(role_scores, key=role_scores.get, reverse=True)[:2]
    if len(top_roles) < 2:
        top_roles.append(top_roles[0] if top_roles else "software")

    return {
        **parsed,
        "role_category": top_roles[0],
        "role_category_secondary": top_roles[1],
        "role_scores": {k: round(v, 3) for k, v in role_scores.items()},
        "seniority": seniority,
        "seniority_scores": {k: round(v, 3) for k, v in seniority_scores.items()},
        "seniority_combined": seniority_combined,
        "jobs": jobs,
        "total_exp_score": experience_score(years),
        "years_experience": years,
        "skills": skills,
        "education": normalized.get("education", "none"),
        "parser_confidence": normalized.get("parser_confidence", "low"),
        "parser_warnings": normalized.get("warnings", []),
    }
