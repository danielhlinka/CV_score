import re
from typing import Optional

SKILLS_BY_CATEGORY = {
    "software": [
        "python", "java", "javascript", "typescript", "c#", "c++", "go", "rust",
        "react", "vue", "angular", "node", "flask", "django", "fastapi", "spring",
        "docker", "kubernetes", "git", "linux", "sql", "postgresql", "mysql",
        "mongodb", "redis", "aws", "azure", "gcp", "terraform", "ci/cd"
    ],
    "data": [
        "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "keras",
        "spark", "hadoop", "tableau", "power bi", "excel", "r", "matlab",
        "machine learning", "deep learning", "nlp", "data analysis", "statistics"
    ],
    "design": [
        "figma", "sketch", "adobe xd", "photoshop", "illustrator", "indesign",
        "ui", "ux", "wireframing", "prototyping", "user research", "typography"
    ],
    "marketing": [
        "seo", "sem", "google ads", "facebook ads", "content marketing",
        "email marketing", "hubspot", "salesforce", "crm", "analytics",
        "copywriting", "social media", "brand strategy"
    ],
    "finance": [
        "accounting", "financial modeling", "bloomberg", "valuation",
        "risk management", "auditing", "tax", "ifrs", "gaap", "budgeting"
    ],
    "ops": [
        "project management", "scrum", "agile", "jira", "confluence", "lean",
        "six sigma", "supply chain", "logistics", "operations", "process improvement"
    ]
}

SENIORITY_TITLE_MAP = {
    "intern": 5, "trainee": 5, "junior": 20, "associate": 25,
    "mid": 40, "medior": 40, "developer": 35, "engineer": 35,
    "analyst": 35, "designer": 35, "specialist": 35, "senior": 65,
    "lead": 75, "principal": 80, "staff": 80, "manager": 70,
    "architect": 80, "director": 85, "head": 85, "vp": 90,
    "cto": 95, "ceo": 95,
}

DEGREE_MAP = {
    "phd": 100, "doctorate": 100, "master": 80, "msc": 80, "mba": 80,
    "bachelor": 60, "bsc": 60, "bc": 60, "associate": 40,
    "bootcamp": 30, "certification": 25, "self-taught": 20, "high school": 10,
}

STEM_FIELDS = [
    "computer science", "software", "engineering", "mathematics",
    "physics", "data science", "information technology", "cybersecurity",
    "electrical", "mechanical", "finance", "economics", "business"
]

SENIORITY_VERBS = [
    "architected", "designed", "led", "managed", "built", "scaled",
    "mentored", "owned", "delivered", "launched", "optimized", "established",
    "directed", "coordinated", "spearheaded", "initiated", "transformed"
]

PERSONALITY_SIGNALS = [
    "open source", "side project", "personal project", "volunteer",
    "hackathon", "competition", "award", "published", "speaker",
    "blog", "teaching", "mentoring", "community", "contributor"
]

EXPERIENCE_HEADERS = [
    "experience", "work experience", "employment", "career",
    "work history", "professional experience", "pracovní zkušenosti",
    "zkušenosti", "zaměstnání"
]

NON_EXPERIENCE_HEADERS = [
    "education", "vzdelání", "vzdělání", "skills", "dovednosti",
    "languages", "jazyky", "certifications", "projects", "projekty",
    "interests", "references", "summary", "objective", "about"
]

def _extract_email(text: str) -> Optional[str]:
    match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    return match.group(0) if match else None


def _extract_phone(text: str) -> Optional[str]:
    match = re.search(r'[\+]?[\d][\d\s\-\.\(\)]{7,}[\d]', text)
    return match.group(0).strip() if match else None


def _extract_skills(text: str) -> tuple:
    text_lower = text.lower()
    matched_skills = []
    category_counts = {cat: 0 for cat in SKILLS_BY_CATEGORY}
    for category, skills in SKILLS_BY_CATEGORY.items():
        for skill in skills:
            if skill in text_lower:
                matched_skills.append(skill)
                category_counts[category] += 1
    dominant = max(category_counts, key=category_counts.get)
    if category_counts[dominant] == 0:
        dominant = "general"
    return matched_skills, dominant


def _extract_experience_section(text: str) -> str:

    lines = text.lower().split("\n")

    in_experience = False
    experience_lines = []

    for line in lines:
        stripped = line.strip()

        # Check if this line is an experience section header
        if any(header in stripped for header in EXPERIENCE_HEADERS):
            in_experience = True
            continue  # skip the header line itself

        # Check if we've hit a new section — stop collecting
        if in_experience and any(header in stripped for header in NON_EXPERIENCE_HEADERS):
            break

        # Collect lines while inside experience section
        if in_experience and stripped:
            experience_lines.append(stripped)

    return "\n".join(experience_lines)


def _extract_years_experience(text: str) -> int:
    current_year = 2026
    experience_text = _extract_experience_section(text)
    scan_text = experience_text if experience_text else text

    # Pattern 1: 2019 - 2022 or 2019 - present
    pattern1 = r'(\d{4})\s*[-–—]\s*(\d{4}|present|current|now|dnes|současnost)'

    # Pattern 2: Month YYYY - Month YYYY (catches "Jún 2025 - September 2025")
    pattern2 = r'[a-zA-ZáäčďéíľĺňóôŕšťúýžÁÄČĎÉÍĽĹŇÓÔŔŠŤÚÝŽ]+\s+(\d{4})\s*[-–—]\s*(?:[a-zA-ZáäčďéíľĺňóôŕšťúýžÁÄČĎÉÍĽĹŇÓÔŔŠŤÚÝŽ]+\s+)?(\d{4}|present|current|now|dnes|jún|september)'

    matches = re.findall(pattern1, scan_text.lower()) + re.findall(pattern2, scan_text)

    start_years = []
    for start, end in matches:
        try:
            s = int(start)
            if 1970 <= s <= current_year:
                start_years.append(s)
        except ValueError:
            continue

    if not start_years:
        return 0

    earliest = min(start_years)
    return min(current_year - earliest, 40)


def _extract_job_titles(text: str) -> list:
    text_lower = text.lower()
    return [t for t in SENIORITY_TITLE_MAP if t in text_lower]


def _extract_education(text: str) -> dict:
    text_lower = text.lower()
    best_degree, best_score = None, 0
    for degree, score in DEGREE_MAP.items():
        if degree in text_lower and score > best_score:
            best_degree, best_score = degree, score
    field_match = next((f for f in STEM_FIELDS if f in text_lower), None)
    return {
        "degree": best_degree or "unknown",
        "degree_score": best_score,
        "field": field_match or "unknown",
        "is_stem": field_match is not None
    }


def _extract_seniority_signals(text: str) -> list:
    text_lower = text.lower()
    return [v for v in SENIORITY_VERBS if v in text_lower]


def _extract_personality_signals(text: str) -> list:
    text_lower = text.lower()
    return [s for s in PERSONALITY_SIGNALS if s in text_lower]


def parse_cv(raw_text: str) -> dict:
    skills, role_category = _extract_skills(raw_text)
    education             = _extract_education(raw_text)
    years                 = _extract_years_experience(raw_text)
    titles                = _extract_job_titles(raw_text)
    seniority_signals     = _extract_seniority_signals(raw_text)
    personality_signals   = _extract_personality_signals(raw_text)
    title_seniority       = max((SENIORITY_TITLE_MAP[t] for t in titles), default=0)

    return {
        "email":                     _extract_email(raw_text),
        "phone":                     _extract_phone(raw_text),
        "skills":                    skills,
        "skills_count":              len(skills),
        "role_category":             role_category,
        "years_experience":          years,
        "job_titles":                titles,
        "title_seniority":           title_seniority,
        "education":                 education,
        "seniority_signals":         seniority_signals,
        "seniority_signals_count":   len(seniority_signals),
        "personality_signals":       personality_signals,
        "personality_signals_count": len(personality_signals),
        "raw_text_length":           len(raw_text),
    }