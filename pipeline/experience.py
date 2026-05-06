import re
import math
from datetime import datetime
from pipeline.extractor import extract_sections

def experience_score(years: float, k: float = 3.0) -> float:
    return round(1 - math.exp(-years / k), 3)

def extract_job_durations(text: str) -> list:
    current_year = datetime.now().year

    # only scan work section to avoid education date false positives
    sections = extract_sections(text)
    work_text = sections.get("work", text)

    month_pattern = r'(?:january|february|march|april|may|june|july|august|september|october|november|december|' \
                    r'január|február|marec|apríl|máj|jún|júl|august|september|október|november|december)\s*'

    pattern = rf'(?:{month_pattern})?(\d{{4}})\s*[-–—]\s*(?:{month_pattern})?(\d{{4}}|present|current|now|dnes|současnost|súčasnosť)'
    matches = re.findall(pattern, work_text.lower())

    jobs = []
    for start, end in matches:
        try:
            s = int(start)
            e = current_year if end in ("present", "current", "now", "dnes", "současnost", "súčasnosť") else int(end)
            if 1970 <= s <= current_year and e >= s:
                years = e - s
                if years == 0:
                    continue  # skip same-year entries
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
    return math.exp(-((years - peak) ** 2) / width)

LEVEL_CURVES = {
    "intern": lambda y: _bell(y, peak=0.5, width=0.5),
    "junior": lambda y: _bell(y, peak=2.0, width=3.0),
    "mid":    lambda y: _bell(y, peak=4.5, width=5.0),
    "senior": lambda y: _bell(y, peak=8.0, width=8.0),
    "lead":   lambda y: 1 - math.exp(-y / 10.0),
}

def combined_seniority(sen_scores: dict, years: int) -> tuple:
    combined = {}
    for level, curve in LEVEL_CURVES.items():
        emb  = sen_scores.get(level, 0)
        exp  = curve(years)
        combined[level] = round(emb * exp, 4)
    return max(combined, key=combined.get), combined