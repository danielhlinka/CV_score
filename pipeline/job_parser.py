def parse_job(form) -> dict:
    raw_skills = form.get("skills", "")
    skills = [s.strip().lower() for s in raw_skills.split(",") if s.strip()]

    return {
        "job_title":      form.get("job_title", "").strip(),
        "seniority":      form.get("seniority", "mid").lower(),
        "years_required": int(form.get("years_required", 0)),
        "skills":         skills,
        "education":      form.get("education", "none").lower(),
        "role_category":  form.get("role_category", "software").lower(),
    }