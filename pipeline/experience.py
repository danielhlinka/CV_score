import re
import math
from datetime import datetime

def experience_score(years: float, k: float = 3.0) -> float:
    return round(1 - math.exp(-years / k), 3)

def extract_job_durations(text: str) -> list:
    current_year = datetime.now().year
    pattern = r'(\d{4})\s*[-–—]\s*(\d{4}|present|current|now|dnes|současnost)'
    matches = re.findall(pattern, text.lower())

    jobs = []
    for start, end in matches:
        try:
            s = int(start)
            e = current_year if end in ("present", "current", "now", "dnes", "současnost") else int(end)
            if 1970 <= s <= current_year and e >= s:
                years = e - s
                jobs.append({
                    "start": s,
                    "end":   e,
                    "years": years,
                    "impact": experience_score(years)
                })
        except ValueError:
            continue

    return jobs

def total_experience_score(jobs: list, k: float = 3.0) -> float:
    total_years = sum(j["years"] for j in jobs)
    return experience_score(total_years, k)

def _bell(years: float, peak: float, width: float) -> float:
    """Score how well `years` fits a seniority level peaking at `peak`."""
    return math.exp(-((years - peak) ** 2) / width)

LEVEL_CURVES = {
    "intern": lambda y: _bell(y, peak=0.5, width=0.5),
    "junior": lambda y: _bell(y, peak=2.0, width=3.0),
    "mid":    lambda y: _bell(y, peak=4.5, width=5.0),
    "senior": lambda y: _bell(y, peak=8.0, width=8.0),
    "lead":   lambda y: 1 - math.exp(-y / 10.0),   # keeps growing, no peak
}

def combined_seniority(sen_scores: dict, years: int) -> tuple:
    combined = {}
    for level, curve in LEVEL_CURVES.items():
        emb  = sen_scores.get(level, 0)
        exp  = curve(years)
        combined[level] = round(emb * exp, 4)
    return max(combined, key=combined.get), combined