import re
from datetime import datetime
from typing import Any

from pipeline import (
    ConfidenceLevel,
    ExperienceEntry,
    NormalizedCV,
    ROLE_SIGNAL_KEYWORDS,
    SENIORITY_SIGNAL_KEYWORDS,
)

from pipeline.extractor import extract_education, extract_skills

PRESENT_TOKENS = {"present", "current", "now", "dnes", "soucasnost", "současnost", "sucasnost", "súčasnosť"}

DATE_RANGE_PATTERN = re.compile(
    r"(?P<start>(?:(?:0?[1-9]|1[0-2])[./-])?(?:19|20)\d{2})\s*[-–—]\s*"
    r"(?P<end>(?:(?:0?[1-9]|1[0-2])[./-])?(?:19|20)\d{2}|present|current|now|dnes|soucasnost|současnost|sucasnost|súčasnosť)",
    re.IGNORECASE,
)

NOISE_LINE_PATTERNS = (
    re.compile(r"^\s*page\s+\d+\s+of\s+\d+\s*$", re.IGNORECASE),
    re.compile(r"^\s*https?://", re.IGNORECASE),
    re.compile(r"^\s*www\.", re.IGNORECASE),
    re.compile(r"^\s*\(?\d{2}/\d{4}\s*[-–—]\s*\d{2}/\d{4}\)?\s*$", re.IGNORECASE),
)

EDUCATION_CONTEXT_PATTERN = re.compile(
    r"\b("
    r"university|college|school|faculty|education|degree|diploma|student|"
    r"bachelor|master|msc|m\.sc|bsc|b\.sc|phd|doctorate|aarhus university|via university"
    r")\b",
    re.IGNORECASE,
)

WORK_CONTEXT_PATTERN = re.compile(
    r"\b("
    r"engineer|architect|consultant|developer|analyst|manager|lead|specialist|"
    r"director|technical|external consultant|revolt|billigence|pwc|ibm|"
    r"s\.r\.o|a\.s\.|inc|corp|llc|gmbh"
    r")\b",
    re.IGNORECASE,
)


def _extract_email(text: str) -> str | None:
    match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    return match.group(0) if match else None


def _extract_phone(text: str) -> str | None:
    match = re.search(r"[\+]?\d[\d\s\-\.\(\)]{7,}\d", text)
    return match.group(0).strip() if match else None


def _is_noise_line(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    if re.fullmatch(r"[\W_]+", stripped):
        return True
    if len(re.sub(r"[^A-Za-z0-9]+", "", stripped)) < 2:
        return True
    if any(p.search(stripped) for p in NOISE_LINE_PATTERNS):
        return True
    if stripped.lower().startswith(("email", "phone", "linkedin", "github", "http")):
        return True
    return False


def _parse_date_token(token: str, *, is_start: bool, now: datetime) -> tuple[int, int] | None:
    lower = token.lower().strip()
    if lower in PRESENT_TOKENS:
        return now.year, now.month

    mm_yyyy = re.fullmatch(r"(0?[1-9]|1[0-2])[./-]((?:19|20)\d{2})", lower)
    if mm_yyyy:
        month = int(mm_yyyy.group(1))
        year = int(mm_yyyy.group(2))
        return year, month

    yyyy = re.fullmatch(r"((?:19|20)\d{2})", lower)
    if yyyy:
        year = int(yyyy.group(1))
        month = 1 if is_start else 12
        return year, month

    return None


def _to_month_index(year: int, month: int) -> int:
    return year * 12 + (month - 1)


def _extract_experience_entries(text: str) -> tuple[list[ExperienceEntry], float, ConfidenceLevel, list[str]]:
    warnings: list[str] = []
    now = datetime.now()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    entries: list[dict[str, Any]] = []
    skipped_education_ranges = 0

    for idx, line in enumerate(lines):
        prev_line = lines[idx - 1].strip() if idx > 0 else ""
        next_line = lines[idx + 1].strip() if idx + 1 < len(lines) else ""
        context_text = f"{prev_line} {line} {next_line}".strip()

        for match in DATE_RANGE_PATTERN.finditer(line):
            prefix_text = line[:match.start()].strip(" ,|:-–—")
            has_education_context = bool(EDUCATION_CONTEXT_PATTERN.search(context_text))
            has_work_context = bool(WORK_CONTEXT_PATTERN.search(context_text))
            if prefix_text and not _is_noise_line(prefix_text) and len(prefix_text) <= 40:
                has_work_context = True

            # Do not count education timeline ranges as work experience.
            if has_education_context and not has_work_context:
                skipped_education_ranges += 1
                continue

            start_token = match.group("start")
            end_token = match.group("end")

            start_date = _parse_date_token(start_token, is_start=True, now=now)
            end_date = _parse_date_token(end_token, is_start=False, now=now)
            if not start_date or not end_date:
                continue

            start_year, start_month = start_date
            end_year, end_month = end_date
            start_idx = _to_month_index(start_year, start_month)
            end_idx = _to_month_index(end_year, end_month)
            if end_idx < start_idx:
                continue

            inline_title = prefix_text
            title = inline_title
            if (not title or _is_noise_line(title)) and prev_line:
                if not _is_noise_line(prev_line):
                    title = prev_line

            if not title or _is_noise_line(title):
                title = "unknown"

            duration_months = (end_idx - start_idx) + 1
            duration_years = round(duration_months / 12.0, 2)

            entries.append(
                {
                    "title": title[:120],
                    "start_year": start_year,
                    "start_month": start_month,
                    "end_year": end_year,
                    "end_month": end_month,
                    "start_index": start_idx,
                    "end_index": end_idx,
                    "years": duration_years,
                    "range_text": f"{start_token} - {end_token}",
                }
            )

    if not entries:
        return [], 0.0, "low", ["No experience date ranges detected from full CV text."]

    if skipped_education_ranges:
        warnings.append(
            f"Skipped {skipped_education_ranges} education-related date range(s) while computing work experience."
        )

    # Deduplicate by title and interval
    dedup: dict[tuple[str, int, int], dict[str, Any]] = {}
    for entry in entries:
        key = (entry["title"].lower(), entry["start_index"], entry["end_index"])
        dedup[key] = entry
    unique_entries = list(dedup.values())
    unique_entries.sort(key=lambda e: e["start_index"])

    # Merge overlapping/adjacent intervals to avoid double counting
    intervals = [(e["start_index"], e["end_index"]) for e in unique_entries]
    merged: list[tuple[int, int]] = []
    for start, end in intervals:
        if not merged:
            merged.append((start, end))
            continue
        last_start, last_end = merged[-1]
        if start <= last_end + 1:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))

    total_months = sum((end - start + 1) for start, end in merged)
    total_years = round(total_months / 12.0, 2)

    recognized_titles = sum(1 for e in unique_entries if e["title"] != "unknown")
    if len(unique_entries) >= 2 and total_years >= 1 and recognized_titles >= 1:
        confidence = "high"
    elif total_years > 0:
        confidence = "medium"
    else:
        confidence = "low"

    if confidence != "high":
        warnings.append("Experience extraction confidence is not high; verify date/title mapping.")

    # Return month-free entries for downstream simplicity
    clean_entries = []
    for entry in sorted(unique_entries, key=lambda e: e["start_index"], reverse=True):
        clean_entries.append(
            {
                "title": entry["title"],
                "start_year": entry["start_year"],
                "end_year": entry["end_year"],
                "years": entry["years"],
                "range_text": entry["range_text"],
            }
        )

    return clean_entries, total_years, confidence, warnings


def _keyword_signals(text: str, mapping: dict[str, tuple[str, ...]]) -> dict[str, int]:
    lowered = text.lower()
    signals: dict[str, int] = {}
    for key, keywords in mapping.items():
        count = 0
        for kw in keywords:
            count += len(re.findall(rf"\b{re.escape(kw.lower())}\b", lowered))
        signals[key] = count
    return signals


def normalize_cv_text(raw_text: str) -> NormalizedCV:
    warnings: list[str] = []
    experience_entries, experience_years, experience_conf, exp_warnings = _extract_experience_entries(raw_text)
    warnings.extend(exp_warnings)

    skills = extract_skills(raw_text)
    education = extract_education(raw_text)

    role_signals = _keyword_signals(raw_text, ROLE_SIGNAL_KEYWORDS)
    seniority_signals = _keyword_signals(raw_text, SENIORITY_SIGNAL_KEYWORDS)

    strongest_role = max(role_signals, key=role_signals.get) if role_signals else "unknown"
    strongest_seniority_signal = max(seniority_signals, key=seniority_signals.get) if seniority_signals else "unknown"

    if not skills:
        warnings.append("No skills detected from CV text.")
    if education == "none":
        warnings.append("No education level confidently detected.")

    # Overall parser confidence prioritizes experience reliability because it strongly impacts score.
    parser_confidence = experience_conf
    if parser_confidence == "high" and len(skills) < 2:
        parser_confidence = "medium"
    if parser_confidence == "medium" and not experience_entries:
        parser_confidence = "low"

    return {
        "contact": {
            "email": _extract_email(raw_text),
            "phone": _extract_phone(raw_text),
        },
        "experience_entries": experience_entries,
        "experience_years": experience_years,
        "experience_confidence": experience_conf,
        "skills": skills,
        "education": education,
        "role_signals": role_signals,
        "seniority_signals": seniority_signals,
        "strongest_role_signal": strongest_role,
        "strongest_seniority_signal": strongest_seniority_signal,
        "parser_confidence": parser_confidence,
        "warnings": warnings,
    }
