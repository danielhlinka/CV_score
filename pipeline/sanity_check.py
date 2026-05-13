import logging

logger = logging.getLogger("pipeline.sanity")

def sanity_check(result: dict) -> None:
    cv       = result.get("cv", {})
    job      = result.get("job", {})
    breakdown = result.get("breakdown", {})
    score    = result.get("final_score", 0)

    logger.info("=" * 45)

    # --- extractor.py values ---
    logger.info("[extractor]  seniority       : %s", cv.get("seniority", "MISSING"))
    logger.info("[extractor]  years_experience: %s", cv.get("years_experience", "MISSING"))
    logger.info("[extractor]  education       : %s", cv.get("education", "MISSING"))
    logger.info("[extractor]  role_category   : %s", cv.get("role_category", "MISSING"))
    logger.info("[extractor]  skills_count    : %d", len(cv.get("skills", [])))
    logger.info("[extractor]  skills          : %s", ", ".join(cv.get("skills", [])) or "NONE")

    # --- matcher.py values ---
    logger.info("[matcher]     skills_score    : %.1f%%", breakdown.get("skills", 0) * 100)
    logger.info("[matcher]     seniority_score : %.1f%%", breakdown.get("seniority", 0) * 100)
    logger.info("[matcher]     experience_score: %.1f%%", breakdown.get("experience", 0) * 100)
    logger.info("[matcher]     education_score : %.1f%%", breakdown.get("education", 0) * 100)
    logger.info("[matcher]     final_score     : %.1f%%", score * 100)

    # --- warnings ---
    if not cv.get("skills"):
        logger.warning("[sanity]     ⚠ No skills extracted — scoring unreliable")
    if cv.get("years_experience", 0) > 50:
        logger.warning("[sanity]     ⚠ years_experience > 50 — likely parse error")
    if score > 1.0 or score < 0:
        logger.warning("[sanity]     ⚠ final_score out of range: %.2f", score)
    if cv.get("seniority") not in ["junior", "mid", "senior", "lead", "executive"]:
        logger.warning("[sanity]     ⚠ Unknown seniority: %s", cv.get("seniority"))
    if not cv.get("education"):
        logger.warning("[sanity]     ⚠ No education detected")

    logger.info("=" * 45)