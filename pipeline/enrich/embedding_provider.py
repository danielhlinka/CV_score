from __future__ import annotations

import hashlib
import re
from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from pipeline.lib.constants import ROLE_CATEGORIES, RoleCategory

_CATEGORY_EMBEDDINGS: dict[str, np.ndarray] = {}


@lru_cache(maxsize=1)
def _get_model():
    """Load sentence-transformer model with offline-first fallback.
    Returns `False` sentinel when model loading is unavailable."""
    try:
        return SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
    except Exception:
        try:
            return SentenceTransformer("all-MiniLM-L6-v2")
        except Exception:
            return False


def _hash_embedding(text: str, dims: int = 384) -> np.ndarray:
    """Build deterministic fallback embedding from token hashing.
    Used when transformer model cannot be loaded at runtime."""
    vec = np.zeros(dims)
    for token in re.findall(r"\w+", text.lower()):
        digest = hashlib.sha1(token.encode("utf-8")).digest()
        idx = int.from_bytes(digest[:4], byteorder="big", signed=False) % dims
        vec[idx] += 1.0
    norm = np.linalg.norm(vec)
    return vec / norm if norm else vec


def embed_text(text: str) -> np.ndarray:
    """Embed text using transformer model or deterministic fallback.
    Returns zero vector for empty/blank input."""
    cleaned = (text or "").strip()
    if not cleaned:
        return np.zeros(384)
    model = _get_model()
    if model is False:
        return _hash_embedding(cleaned)
    return model.encode(cleaned)


def get_embedding(text: str) -> np.ndarray:
    """Public alias for text embedding generation.
    Preserves compatibility with existing import sites."""
    return embed_text(text)


def classify_role(title: str) -> RoleCategory:
    """Classify role category by cosine similarity to role labels.
    Caches label embeddings to avoid repeated computation."""
    title_emb = embed_text(title)
    scores = {}
    for category in ROLE_CATEGORIES:
        if category not in _CATEGORY_EMBEDDINGS:
            _CATEGORY_EMBEDDINGS[category] = embed_text(category)
        scores[category] = float(cosine_similarity([title_emb], [_CATEGORY_EMBEDDINGS[category]])[0][0])
    return max(scores, key=scores.get)
