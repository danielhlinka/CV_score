from functools import cache

from pipeline import (
    EnrichedCV,
    ParsedCV,
    ROLE_TEMPLATES,
    SENIORITY_TEMPLATES,
)
from pipeline.lib.experience import combined_seniority, experience_score
from pipeline.lib.semantic import Embedding, memoized_embedding, template_scores


@cache
def _get_role_template_embeddings() -> dict[str, Embedding]:
    """Compute cached embeddings for legacy role template access path.
    Maintained for backward compatibility with older import sites/tests."""
    return {role: memoized_embedding(template) for role, template in ROLE_TEMPLATES.items()}


@cache
def _get_seniority_template_embeddings() -> dict[str, Embedding]:
    """Compute cached embeddings for legacy seniority templates.
    Mirrors behavior of the reorganized enrichment module."""
    return {level: memoized_embedding(template) for level, template in SENIORITY_TEMPLATES.items()}


def _normalized_signal_scores(signals: dict[str, int]) -> dict[str, float]:
    """Normalize keyword count signals for backward-compatible scoring.
    Handles empty and zero-valued maps without division errors."""
    if not signals:
        return {}
    max_value = max(signals.values())
    if max_value <= 0:
        return {k: 0.0 for k in signals}
    return {k: float(v) / float(max_value) for k, v in signals.items()}


def enrich_cv(parsed: ParsedCV) -> EnrichedCV:
    """Legacy enrichment entrypoint kept stable for compatibility.
    Produces the same enriched payload contract as before refactor."""
    normalized = parsed["normalized"]
    skills = normalized.get("skills", [])
    jobs = normalized.get("experience_entries", [])
    years = float(normalized.get("experience_years", 0.0))

    role_signals = normalized.get("role_signals", {})
    role_signal_scores = _normalized_signal_scores(role_signals)

    seniority_signals = normalized.get("seniority_signals", {})
    seniority_signal_scores = _normalized_signal_scores(seniority_signals)

    role_hint = normalized.get("strongest_role_signal", "")
    titles_text = " ".join(j.get("title", "") for j in jobs if j.get("title") and j.get("title") != "unknown")

    # Embeddings are built only from normalized fields (skills, titles, role hints), not raw CV blobs.
    semantic_profile = " ".join(
        part for part in [" ".join(skills), titles_text, role_hint] if part
    )
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
    sen_sem_scores = template_scores(seniority_emb, seniority_template_embeddings)

    sen_scores = {}
    for level in sen_sem_scores:
        semantic = sen_sem_scores.get(level, 0.0)
        signal = seniority_signal_scores.get(level, 0.0)
        sen_scores[level] = round((semantic * 0.75) + (signal * 0.25), 4)

    seniority, seniority_combined = combined_seniority(sen_scores, int(round(years)))

    top_roles = sorted(role_scores, key=role_scores.get, reverse=True)[:2]
    if len(top_roles) < 2:
        top_roles.append(top_roles[0] if top_roles else "software")

    return {
        **parsed,
        "role_category": top_roles[0],
        "role_category_secondary": top_roles[1],
        "role_scores": {k: round(v, 3) for k, v in role_scores.items()},
        "seniority": seniority,
        "seniority_scores": {k: round(v, 3) for k, v in sen_scores.items()},
        "seniority_combined": seniority_combined,
        "jobs": jobs,
        "total_exp_score": experience_score(years),
        "years_experience": years,
        "skills": skills,
        "education": normalized.get("education", "none"),
        "parser_confidence": normalized.get("parser_confidence", "low"),
        "parser_warnings": normalized.get("warnings", []),
    }
