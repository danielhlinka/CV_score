from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from pipeline.constants import ConfidenceLevel
from pipeline.contracts import ExperienceEntry

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

DATE_TOKEN_MM_YYYY_PATTERN = re.compile(r"(0?[1-9]|1[0-2])[./-]((?:19|20)\d{2})")
DATE_TOKEN_YYYY_PATTERN = re.compile(r"((?:19|20)\d{2})")


@dataclass(frozen=True, slots=True)
class _ParsedDateToken:
    year: int
    month: int

    @property
    def month_index(self) -> int:
        return _to_month_index(self.year, self.month)


@dataclass(frozen=True, slots=True)
class _ExperienceCandidate:
    title: str
    start_year: int
    start_month: int
    end_year: int
    end_month: int
    start_index: int
    end_index: int
    years: float
    range_text: str

    @property
    def dedupe_key(self) -> tuple[str, int, int]:
        return (self.title.lower(), self.start_index, self.end_index)

    def as_entry(self) -> ExperienceEntry:
        return {
            "title": self.title,
            "start_year": self.start_year,
            "end_year": self.end_year,
            "years": self.years,
            "range_text": self.range_text,
        }


def _is_noise_line(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    if re.fullmatch(r"[\W_]+", stripped):
        return True
    if len(re.sub(r"[^A-Za-z0-9]+", "", stripped)) < 2:
        return True
    if any(pattern.search(stripped) for pattern in NOISE_LINE_PATTERNS):
        return True
    if stripped.lower().startswith(("email", "phone", "linkedin", "github", "http")):
        return True
    return False


def _parse_date_token(token: str, *, is_start: bool, now: datetime) -> tuple[int, int] | None:
    lower = token.lower().strip()
    if lower in PRESENT_TOKENS:
        return now.year, now.month

    mm_yyyy = DATE_TOKEN_MM_YYYY_PATTERN.fullmatch(lower)
    if mm_yyyy:
        month = int(mm_yyyy.group(1))
        year = int(mm_yyyy.group(2))
        return year, month

    yyyy = DATE_TOKEN_YYYY_PATTERN.fullmatch(lower)
    if yyyy:
        year = int(yyyy.group(1))
        month = 1 if is_start else 12
        return year, month

    return None


def _to_month_index(year: int, month: int) -> int:
    return year * 12 + (month - 1)


def _resolve_line_context(lines: list[str], index: int) -> tuple[str, str]:
    prev_line = lines[index - 1].strip() if index > 0 else ""
    next_line = lines[index + 1].strip() if index + 1 < len(lines) else ""
    return prev_line, next_line


def _has_work_and_education_context(context_text: str, prefix_text: str) -> tuple[bool, bool]:
    has_education_context = bool(EDUCATION_CONTEXT_PATTERN.search(context_text))
    has_work_context = bool(WORK_CONTEXT_PATTERN.search(context_text))

    if prefix_text and not _is_noise_line(prefix_text) and len(prefix_text) <= 40:
        has_work_context = True

    return has_education_context, has_work_context


def _resolve_title(prefix_text: str, prev_line: str) -> str:
    title = prefix_text
    if (not title or _is_noise_line(title)) and prev_line and not _is_noise_line(prev_line):
        title = prev_line
    if not title or _is_noise_line(title):
        return "unknown"
    return title[:120]


def _parse_date_tokens(
    start_token: str,
    end_token: str,
    *,
    now: datetime,
) -> tuple[_ParsedDateToken, _ParsedDateToken] | None:
    parsed_start = _parse_date_token(start_token, is_start=True, now=now)
    parsed_end = _parse_date_token(end_token, is_start=False, now=now)
    if not parsed_start or not parsed_end:
        return None

    start_date = _ParsedDateToken(year=parsed_start[0], month=parsed_start[1])
    end_date = _ParsedDateToken(year=parsed_end[0], month=parsed_end[1])
    if end_date.month_index < start_date.month_index:
        return None

    return start_date, end_date


def _build_candidate_from_match(
    *,
    line: str,
    prev_line: str,
    next_line: str,
    match: re.Match[str],
    now: datetime,
) -> tuple[_ExperienceCandidate | None, bool]:
    prefix_text = line[: match.start()].strip(" ,|:-–—")
    context_text = f"{prev_line} {line} {next_line}".strip()
    has_education_context, has_work_context = _has_work_and_education_context(context_text, prefix_text)

    if has_education_context and not has_work_context:
        return None, True

    start_token = match.group("start")
    end_token = match.group("end")
    parsed_dates = _parse_date_tokens(start_token, end_token, now=now)
    if not parsed_dates:
        return None, False

    start_date, end_date = parsed_dates
    duration_months = (end_date.month_index - start_date.month_index) + 1

    return (
        _ExperienceCandidate(
            title=_resolve_title(prefix_text, prev_line),
            start_year=start_date.year,
            start_month=start_date.month,
            end_year=end_date.year,
            end_month=end_date.month,
            start_index=start_date.month_index,
            end_index=end_date.month_index,
            years=round(duration_months / 12.0, 2),
            range_text=f"{start_token} - {end_token}",
        ),
        False,
    )


def _deduplicate_candidates(candidates: list[_ExperienceCandidate]) -> list[_ExperienceCandidate]:
    deduplicated: dict[tuple[str, int, int], _ExperienceCandidate] = {}
    for candidate in candidates:
        deduplicated[candidate.dedupe_key] = candidate

    unique_candidates = list(deduplicated.values())
    unique_candidates.sort(key=lambda candidate: candidate.start_index)
    return unique_candidates


def _merge_intervals(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
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
    return merged


def _determine_experience_confidence(
    entries: list[_ExperienceCandidate], total_years: float
) -> ConfidenceLevel:
    recognized_titles = sum(1 for entry in entries if entry.title != "unknown")
    if len(entries) >= 2 and total_years >= 1 and recognized_titles >= 1:
        return "high"
    if total_years > 0:
        return "medium"
    return "low"


def _build_experience_warnings(
    *, skipped_education_ranges: int, confidence: ConfidenceLevel
) -> list[str]:
    warnings: list[str] = []
    if skipped_education_ranges:
        warnings.append(
            f"Skipped {skipped_education_ranges} education-related date range(s) while computing work experience."
        )
    if confidence != "high":
        warnings.append("Experience extraction confidence is not high; verify date/title mapping.")
    return warnings


def _clean_experience_entries(entries: list[_ExperienceCandidate]) -> list[ExperienceEntry]:
    return [
        candidate.as_entry()
        for candidate in sorted(entries, key=lambda candidate: candidate.start_index, reverse=True)
    ]


def parse_experience_entries(text: str) -> tuple[list[ExperienceEntry], float, ConfidenceLevel, list[str]]:
    now = datetime.now()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    candidates: list[_ExperienceCandidate] = []
    skipped_education_ranges = 0

    for index, line in enumerate(lines):
        prev_line, next_line = _resolve_line_context(lines, index)
        for match in DATE_RANGE_PATTERN.finditer(line):
            candidate, skipped_as_education = _build_candidate_from_match(
                line=line,
                prev_line=prev_line,
                next_line=next_line,
                match=match,
                now=now,
            )
            if skipped_as_education:
                skipped_education_ranges += 1
                continue
            if candidate:
                candidates.append(candidate)

    if not candidates:
        return [], 0.0, "low", ["No experience date ranges detected from full CV text."]

    unique_candidates = _deduplicate_candidates(candidates)
    intervals = [(candidate.start_index, candidate.end_index) for candidate in unique_candidates]
    merged_intervals = _merge_intervals(intervals)

    total_months = sum((end - start + 1) for start, end in merged_intervals)
    total_years = round(total_months / 12.0, 2)
    confidence = _determine_experience_confidence(unique_candidates, total_years)
    warnings = _build_experience_warnings(
        skipped_education_ranges=skipped_education_ranges, confidence=confidence
    )
    clean_entries = _clean_experience_entries(unique_candidates)

    return clean_entries, total_years, confidence, warnings
