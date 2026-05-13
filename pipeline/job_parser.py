from collections.abc import Mapping, Set

from werkzeug.exceptions import BadRequest

from pipeline import JobProfile, VALID_EDUCATION, VALID_ROLE_CATEGORIES, VALID_SENIORITY


def _normalized_choice(
    value: str | None,
    *,
    field_name: str,
    allowed_values: Set[str],
    default: str,
) -> str:
    candidate = (value or "").strip().lower()
    if not candidate:
        return default
    if candidate not in allowed_values:
        raise BadRequest(
            f"Invalid '{field_name}' value. Allowed: {', '.join(sorted(allowed_values))}."
        )
    return candidate


def _parse_years_required(form: Mapping[str, str]) -> int:
    raw_years = str(form.get("years_required", "")).strip()
    if raw_years == "":
        return 0
    try:
        years_required = int(raw_years)
    except ValueError as exc:
        raise BadRequest("'years_required' must be a whole number.") from exc

    if years_required < 0:
        raise BadRequest("'years_required' cannot be negative.")
    if years_required > 50:
        raise BadRequest("'years_required' is unrealistically high.")
    return years_required


def parse_job(form: Mapping[str, str]) -> JobProfile:
    job_title = str(form.get("job_title", "")).strip()
    if not job_title:
        raise BadRequest("'job_title' is required.")

    raw_skills = str(form.get("skills", ""))
    skills = []
    seen = set()
    for skill in raw_skills.split(","):
        normalized = skill.strip().lower()
        if normalized and normalized not in seen:
            seen.add(normalized)
            skills.append(normalized)

    return {
        "job_title": job_title,
        "seniority": _normalized_choice(
            form.get("seniority"),
            field_name="seniority",
            allowed_values=VALID_SENIORITY,
            default="mid",
        ),
        "years_required": _parse_years_required(form),
        "skills": skills,
        "education": _normalized_choice(
            form.get("education"),
            field_name="education",
            allowed_values=VALID_EDUCATION,
            default="none",
        ),
        "role_category": _normalized_choice(
            form.get("role_category"),
            field_name="role_category",
            allowed_values=VALID_ROLE_CATEGORIES,
            default="software",
        ),
    }
