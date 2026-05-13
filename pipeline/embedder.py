from sklearn.metrics.pairwise import cosine_similarity
from pipeline.embeddings import get_embedding, model
from pipeline.experience import extract_job_durations, total_experience_score, combined_seniority
from pipeline.extractor import extract_skills, extract_education

ROLE_TEMPLATES = {
    "software": (
        "A software developer and programmer writing code in Python, Java, C, PHP, HTML, CSS. "
        "Studying ICT and software engineering. Building applications, scripts and web development. "
        "Internship at IBM developer team. Interested in AI, machine learning and programming."
    ),
    "data": (
        "A data analyst or data scientist working with machine learning, statistics, pandas, "
        "numpy, and data visualization. Analyses datasets and builds predictive models."
    ),
    "design": (
        "A UI/UX designer creating wireframes and prototypes in Figma. Focused on user research, "
        "visual design, graphic design, typography, colour theory and improving user interfaces. "
        "No programming involved."
    ),
    "ops": (
        "A project manager or operations specialist working with logistics, supply chain, "
        "warehouse management, agile, scrum, and process improvement."
    ),
    "finance": (
        "An accountant or financial analyst working with budgeting, auditing, financial modeling, "
        "risk management, and reporting."
    ),
    "marketing": (
        "A digital marketer running SEO, social media campaigns, content creation, "
        "Google Ads, and managing CRM tools."
    ),
}

SENIORITY_TEMPLATES = {
    "intern":  "student intern learning first experience trainee",
    "junior":  "junior developer 1 year entry level learning growing",
    "mid":     "developer 3 years experience independent projects delivered",
    "senior":  "senior led team architected scaled mentored owned delivered",
    "lead":    "lead manager director principal staff architected strategic vision",
}

template_embeddings  = {k: model.encode(v) for k, v in ROLE_TEMPLATES.items()}
seniority_embeddings = {k: model.encode(v) for k, v in SENIORITY_TEMPLATES.items()}


def enrich_cv(parsed: dict) -> dict:
    text = parsed["raw_text"]
    cv_emb = get_embedding(text)

    role_scores = {
        k: float(cosine_similarity([cv_emb], [v])[0][0])
        for k, v in template_embeddings.items()
    }
    sen_scores = {
        k: float(cosine_similarity([cv_emb], [v])[0][0])
        for k, v in seniority_embeddings.items()
    }

    jobs = extract_job_durations(text)
    years = sum(j["years"] for j in jobs)
    seniority, seniority_combined = combined_seniority(sen_scores, years)

    top_roles = sorted(role_scores, key=role_scores.get, reverse=True)[:2]
    parsed["role_category"] = top_roles[0]
    parsed["role_category_secondary"] = top_roles[1]
    parsed["role_scores"] = {k: round(v, 3) for k, v in role_scores.items()}
    parsed["role_scores"]        = {k: round(v, 3) for k, v in role_scores.items()}
    parsed["seniority"]          = seniority
    parsed["seniority_scores"]   = {k: round(v, 3) for k, v in sen_scores.items()}
    parsed["seniority_combined"] = seniority_combined
    parsed["jobs"]               = extract_job_durations(text)
    parsed["total_exp_score"]    = total_experience_score(jobs)
    parsed["years_experience"]   = years
    parsed["skills"]             = extract_skills(text)
    parsed["education"]          = extract_education(text)

    return parsed