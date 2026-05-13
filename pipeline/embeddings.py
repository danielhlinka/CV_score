import hashlib
import re

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from pipeline import ROLE_CATEGORIES, RoleCategory

_MODEL = None

_CATEGORY_EMBEDDINGS: dict[str, np.ndarray] = {}


def _get_model():
    global _MODEL
    if _MODEL is not None:
        return _MODEL
    try:
        _MODEL = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
    except Exception:
        try:
            _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception:
            _MODEL = False
    return _MODEL


def _hash_embedding(text: str, dims: int = 384) -> np.ndarray:
    vec = np.zeros(dims)
    for token in re.findall(r"\w+", text.lower()):
        digest = hashlib.sha1(token.encode("utf-8")).digest()
        idx = int.from_bytes(digest[:4], byteorder="big", signed=False) % dims
        vec[idx] += 1.0
    norm = np.linalg.norm(vec)
    return vec / norm if norm else vec


def embed_text(text: str) -> np.ndarray:
    cleaned = (text or "").strip()
    if not cleaned:
        return np.zeros(384)
    model = _get_model()
    if model is False:
        return _hash_embedding(cleaned)
    return model.encode(cleaned)


def get_embedding(text: str) -> np.ndarray:
    # Backward-compatible alias used across the project.
    return embed_text(text)


def classify_role(title: str) -> RoleCategory:
    title_emb = embed_text(title)
    scores = {}
    for cat in ROLE_CATEGORIES:
        if cat not in _CATEGORY_EMBEDDINGS:
            _CATEGORY_EMBEDDINGS[cat] = embed_text(cat)
        scores[cat] = float(cosine_similarity([title_emb], [_CATEGORY_EMBEDDINGS[cat]])[0][0])
    return max(scores, key=scores.get)
