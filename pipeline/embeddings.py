import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer('all-MiniLM-L6-v2')

SECTION_HEADERS = {
    "skills":    ["skills", "skill"],
    "education": ["education"],
}

SECTION_WEIGHTS = {
    "skills":    0.55,
    "education": 0.35,
    "other":     0.10,
}

ROLE_CATEGORIES = [
    "software", "data", "design", "ops",
    "finance", "marketing", "logistics", "food_service"
]

_CATEGORY_EMBEDDINGS = {}


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


def get_embedding(text: str) -> np.ndarray:
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


def classify_role(title: str) -> str:
    title_emb = get_embedding(title)
    scores = {}
    for cat in ROLE_CATEGORIES:
        if cat not in _CATEGORY_EMBEDDINGS:
            _CATEGORY_EMBEDDINGS[cat] = get_embedding(cat)
        scores[cat] = float(cosine_similarity([title_emb], [_CATEGORY_EMBEDDINGS[cat]])[0][0])
    return max(scores, key=scores.get)