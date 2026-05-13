import re
import math
from datetime import datetime
from pipeline.extractor import extract_sections
from pipeline.embeddings import classify_role


def experience_score(years: float, k: float = 3.0) -> float:
    return round(1 - math.exp(-years / k), 3)

skip_prefixes = ("phone", "email", "tel", "address", "linkedin", "github", "http")

def extract_job_durations(text: str) -> list:
    current_year = datetime.now().year

    sections = extract_sections(text)
    work_text = sections.get("work", text)

    month_pattern = r'(?:january|february|march|april|may|june|july|august|september|october|november|december|' \
                    r'január|február|marec|apríl|máj|jún|júl|august|september|október|november|december)\s*'

    # Title: 3-60 chars on the same line, separated from date by whitespace/dash/comma
    pattern = rf'^([^\n]{{3,60}}?)\s*[,\-–—|]?\s*(?:{month_pattern})?(\d{{4}})\s*[-–—]\s*(?:{month_pattern})?(\d{{4}}|present|current|now|dnes|současnost|súčasnosť)'

    matches = re.findall(pattern, work_text.lower(), re.MULTILINE)

    jobs = []
    for title, start, end in matches:
        try:
            s = int(start)
            e = current_year if end in ("present", "current", "now", "dnes", "současnost", "súčasnosť") else int(end)
            if 1970 <= s <= current_year and e >= s:
                years = e - s
                if years == 0:
                    continue
                clean_title = title.strip(" ,—–-|")


                if any(clean_title.lower().startswith(p) for p in skip_prefixes):
                    continue

                jobs.append({
                    "title":         clean_title if clean_title else "unknown",
                    "start":         s,
                    "end":           e,
                    "years":         years,
                    "impact":        experience_score(years),
                    "role_category": classify_role(clean_title) if clean_title else "unknown"
                })
        except ValueError:
            continue

    return jobs


def total_experience_score(jobs: list, k: float = 3.0) -> float:
    if not jobs:
        return 0.0

    # Merge overlapping date ranges before summing
    intervals = sorted((j["start"], j["end"]) for j in jobs)
    merged = [intervals[0]]
    for start, end in intervals[1:]:
        if start <= merged[-1][1]:  # overlaps with last interval
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    total_years = sum(end - start for start, end in merged)
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