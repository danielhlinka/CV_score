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
    return float(cosine_similarity([left], [right])[0][0])


def template_scores(profile: Embedding, templates: Mapping[str, Embedding]) -> dict[str, float]:
    return {label: cosine_score(profile, template) for label, template in templates.items()}


def best_cosine_score(target: Embedding, candidates: Iterable[Embedding], default: float = 0.0) -> float:
    return max((cosine_score(target, candidate) for candidate in candidates), default=default)


@lru_cache(maxsize=4096)
def memoized_embedding(text: str) -> Embedding:
    return get_embedding(text)
