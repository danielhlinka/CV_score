import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from pipeline.experience import extract_job_durations, total_experience_score, combined_seniority

model = SentenceTransformer('all-MiniLM-L6-v2')

ROLE_TEMPLATES = {
    "software": (
        "A software developer studying ICT specialization at technical high school. "
        "Completed an internship at IBM in the Devices Department attending developer team consultations. "
        "Programs in Python, Java, JavaScript, PHP and HTML. Builds applications and is interested in AI development."
    ),
    "data": (
        "A data analyst or data scientist working with machine learning, statistics, pandas, "
        "numpy, and data visualization. Analyses datasets and builds predictive models."
    ),
    "design": (
        "A UI/UX designer creating wireframes and prototypes in Figma. Focused on user research, "
        "visual design, and improving user interfaces."
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

SECTION_HEADERS = {
    "skills":     ["skills", "skill"],
    "education":  ["education"],
}

SECTION_WEIGHTS = {
    "skills":     0.55,
    "education":  0.35,
    "other":      0.10,
}

template_embeddings  = {k: model.encode(v) for k, v in ROLE_TEMPLATES.items()}
seniority_embeddings = {k: model.encode(v) for k, v in SENIORITY_TEMPLATES.items()}


def _split_sections(text: str) -> dict:
    lines = text.splitlines()
    current = "other"
    sections = {k: [] for k in list(SECTION_HEADERS.keys()) + ["other"]}

    for line in lines:
        lower = line.lower().strip()
        matched = False
        for section, headers in SECTION_HEADERS.items():
            if any(lower == h for h in headers):
                current = section
                matched = True
                break
        if not matched:
            sections[current].append(line)

    return {k: "\n".join(v) for k, v in sections.items()}


def _weighted_embedding(text: str) -> np.ndarray:
    sections = _split_sections(text)
    cv_emb = np.zeros(384)
    total_weight = 0

    for section, content in sections.items():
        if content.strip():
            emb = model.encode(content)
            w = SECTION_WEIGHTS.get(section, 0.1)
            cv_emb += emb * w
            total_weight += w

    return cv_emb / total_weight if total_weight > 0 else cv_emb


def enrich_cv(parsed: dict) -> dict:
    text = parsed["raw_text"]
    cv_emb = _weighted_embedding(text)

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

    parsed["role_category"]      = max(role_scores, key=role_scores.get)
    parsed["role_scores"]        = {k: round(v, 3) for k, v in role_scores.items()}
    parsed["seniority"]          = seniority
    parsed["seniority_scores"]   = {k: round(v, 3) for k, v in sen_scores.items()}
    parsed["seniority_combined"] = seniority_combined
    parsed["jobs"]               = extract_job_durations(text)
    parsed["total_exp_score"]    = total_experience_score(jobs)
    parsed["years_experience"]   = years

    return parsed