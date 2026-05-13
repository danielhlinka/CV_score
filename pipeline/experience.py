import math


def experience_score(years: float, k: float = 3.0) -> float:
    return round(1 - math.exp(-years / k), 3)


def _bell(years: float, peak: float, width: float) -> float:
    return math.exp(-((years - peak) ** 2) / width)

LEVEL_CURVES = {
    "intern": lambda y: _bell(y, peak=0.5, width=0.5),
    "junior": lambda y: _bell(y, peak=2.0, width=3.0),
    "mid":    lambda y: _bell(y, peak=4.5, width=5.0),
    "senior": lambda y: _bell(y, peak=8.0, width=8.0),
    "lead":   lambda y: 1 - math.exp(-y / 10.0),
}


def combined_seniority(sen_scores: dict[str, float], years: int) -> tuple[str, dict[str, float]]:
    combined = {}
    for level, curve in LEVEL_CURVES.items():
        emb = sen_scores.get(level, 0.0)
        exp = curve(years)
        combined[level] = round(emb * exp, 4)
    return max(combined, key=combined.get), combined
