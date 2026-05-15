from __future__ import annotations

from collections.abc import Iterable, Mapping
from functools import lru_cache
from typing import Any

import numpy as np
from numpy.typing import NDArray
from sklearn.metrics.pairwise import cosine_similarity

from pipeline.enrich.embedding_provider import get_embedding

Embedding = NDArray[np.floating[Any]]


def cosine_score(left: Embedding, right: Embedding) -> float:
    """Compute cosine similarity between two embedding vectors.
    Returns a Python float for downstream serialization friendliness."""
    return float(cosine_similarity([left], [right])[0][0])


def template_scores(profile: Embedding, templates: Mapping[str, Embedding]) -> dict[str, float]:
    """Score one profile embedding against labeled template embeddings.
    Produces per-label cosine similarities for ranking/selection."""
    return {label: cosine_score(profile, template) for label, template in templates.items()}


def best_cosine_score(target: Embedding, candidates: Iterable[Embedding], default: float = 0.0) -> float:
    """Return highest cosine similarity from candidate embedding set.
    Falls back to `default` when candidate iterable is empty."""
    return max((cosine_score(target, candidate) for candidate in candidates), default=default)


@lru_cache(maxsize=4096)
def memoized_embedding(text: str) -> Embedding:
    """Cache text embeddings to avoid duplicate model/hashing work.
    Shared cache improves throughput across scoring components."""
    return get_embedding(text)
