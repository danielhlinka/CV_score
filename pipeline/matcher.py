from sklearn.metrics.pairwise import cosine_similarity
from pipeline.embedder import get_embedding

WEIGHTS = {
    "skills":     0.40,
    "seniority":  0.25,
    "experience": 0.25,
    "role":       0.05,
    "education":  0.05,
}

EDUCATION_LEVELS = {
    "none": 0, "high_school": 1,
    "bachelor": 2, "master": 3, "phd": 4
}

SENIORITY_LEVELS = {
    "intern": 0, "junior": 1,
    "mid": 2, "senior": 3, "lead": 4
}


def _skills_score(cv: dict, job: dict) -> float:
    if not job["skills"]:
        return 1.0
    cv_skills = [s.lower() for s in cv.get("skills", [])]
    matched = sum(1 for s in job["skills"] if s in cv_skills)
    exact = matched / len(job["skills"])

    if exact < 1.0:
        unmatched = [s for s in job["skills"] if s not in cv_skills]
        cv_embs = {s: get_embedding(s) for s in cv_skills}

        per_skill_scores = []
        for req_skill in unmatched:
            req_emb = get_embedding(req_skill)
            best = max(
                (float(cosine_similarity([req_emb], [cv_embs[cs]])[0][0]) for cs in cv_skills),
                default=0.0
            )
            per_skill_scores.append(best)
        soft = sum(per_skill_scores) / len(per_skill_scores) if per_skill_scores else 0.0
        return round((exact + soft) / 2, 3)

    return round(exact, 3)

def _seniority_score(cv: dict, job: dict) -> float:
    cv_level  = SENIORITY_LEVELS.get(cv.get("seniority", "junior"), 1)
    job_level = SENIORITY_LEVELS.get(job.get("seniority", "mid"), 2)
    diff = abs(cv_level - job_level)
    return round(max(0.0, 1.0 - diff * 0.25), 3)


def _experience_score(cv: dict, job: dict) -> float:
    job_years = job.get("years_required", 0)
    if job_years == 0:
        return 1.0
    # Always use total years — broken role_category on jobs makes category filtering unreliable
    cv_years = cv.get("years_experience", 0)
    ratio = cv_years / job_years
    return round(min(ratio, 1.0), 3)


def _role_score(cv: dict, job: dict) -> float:
    # Compares CV's detected role category against manually selected job category
    cv_role  = cv.get("role_category", "").lower()
    job_role = job.get("role_category", "").lower()
    if not cv_role or not job_role:
        return 0.5
    return 1.0 if cv_role == job_role else 0.2


def _education_score(cv: dict, job: dict) -> float:
    cv_level  = EDUCATION_LEVELS.get(cv.get("education", "none"), 0)
    job_level = EDUCATION_LEVELS.get(job.get("education", "none"), 0)
    if cv_level >= job_level:
        return 1.0
    diff = job_level - cv_level
    return round(max(0.0, 1.0 - diff * 0.25), 3)


def match(cv: dict, job: dict) -> dict:
    scores = {
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
        "cv":          cv,
        "job":         job,
    }