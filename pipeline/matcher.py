from sklearn.metrics.pairwise import cosine_similarity
from pipeline.embedder import get_embedding

WEIGHTS = {
    "skills":     0.40,
    "seniority":  0.25,
    "experience": 0.20,
    "title":      0.10,
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

    # soft match for near misses via embedding
    if exact < 1.0:
        unmatched = [s for s in job["skills"] if s not in cv_skills]
        soft_scores = []
        for req_skill in unmatched:
            req_emb = get_embedding(req_skill)
            for cv_skill in cv_skills:
                cv_emb = get_embedding(cv_skill)
                sim = float(cosine_similarity([req_emb], [cv_emb])[0][0])
                soft_scores.append(sim)
        soft = max(soft_scores) if soft_scores else 0.0
        return round((exact + soft) / 2, 3)

    return round(exact, 3)


def _seniority_score(cv: dict, job: dict) -> float:
    cv_level  = SENIORITY_LEVELS.get(cv.get("seniority", "junior"), 1)
    job_level = SENIORITY_LEVELS.get(job.get("seniority", "mid"), 2)
    diff = abs(cv_level - job_level)
    return round(max(0.0, 1.0 - diff * 0.25), 3)


def _experience_score(cv: dict, job: dict) -> float:
    cv_years  = cv.get("years_experience", 0)
    job_years = job.get("years_required", 0)
    if job_years == 0:
        return 1.0
    ratio = cv_years / job_years
    return round(min(ratio, 1.0), 3)   # cap at 1.0, no bonus for overqualified


def _title_score(cv: dict, job: dict) -> float:
    cv_title  = cv.get("role_category", "")
    job_title = job.get("job_title", "")
    if not cv_title or not job_title:
        return 0.5
    cv_emb  = get_embedding(cv_title)
    job_emb = get_embedding(job_title)
    return round(float(cosine_similarity([cv_emb], [job_emb])[0][0]), 3)


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
        "title":      _title_score(cv, job),
        "education":  _education_score(cv, job),
    }

    final = sum(scores[k] * WEIGHTS[k] for k in scores)

    return {
        "final_score": round(final, 3),
        "breakdown":   scores,
        "cv":          cv,
        "job":         job,
    }