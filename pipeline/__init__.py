from __future__ import annotations

from typing import Final, Literal, NotRequired, TypedDict

RoleCategory = Literal[
    "software",
    "data",
    "management",
    "design",
    "ops",
    "finance",
    "marketing",
    "logistics",
    "food_service",
]
JobRoleCategory = Literal["software", "management", "data", "design", "ops", "finance", "marketing"]
SeniorityLevel = Literal["intern", "junior", "mid", "senior", "lead"]
EducationLevel = Literal["none", "high_school", "bachelor", "master", "phd"]
ConfidenceLevel = Literal["low", "medium", "high"]

ROLE_CATEGORIES: Final[tuple[RoleCategory, ...]] = (
    "software",
    "data",
    "management",
    "design",
    "ops",
    "finance",
    "marketing",
    "logistics",
    "food_service",
)
JOB_ROLE_CATEGORIES: Final[tuple[JobRoleCategory, ...]] = (
    "software",
    "management",
    "data",
    "design",
    "ops",
    "finance",
    "marketing",
)
SENIORITY_ORDER: Final[tuple[SeniorityLevel, ...]] = ("intern", "junior", "mid", "senior", "lead")
EDUCATION_ORDER: Final[tuple[EducationLevel, ...]] = (
    "none",
    "high_school",
    "bachelor",
    "master",
    "phd",
)

VALID_ROLE_CATEGORIES: Final[frozenset[str]] = frozenset(JOB_ROLE_CATEGORIES)
VALID_SENIORITY: Final[frozenset[str]] = frozenset(SENIORITY_ORDER)
VALID_EDUCATION: Final[frozenset[str]] = frozenset(EDUCATION_ORDER)

SENIORITY_LEVEL_RANK: Final[dict[SeniorityLevel, int]] = {
    level: idx for idx, level in enumerate(SENIORITY_ORDER)
}
EDUCATION_LEVEL_RANK: Final[dict[EducationLevel, int]] = {
    level: idx for idx, level in enumerate(EDUCATION_ORDER)
}

ROLE_TEMPLATES: Final[dict[JobRoleCategory, str]] = {
    "software": (
        "software developer backend engineer api python java javascript microservices architecture "
        "code quality testing"
    ),
    "data": (
        "data architect data engineer analytics engineering data warehouse etl elt sql spark "
        "databricks snowflake pipeline orchestration"
    ),
    "management": (
        "engineering manager people leadership stakeholder management delivery roadmap "
        "organizational leadership strategy cross functional execution"
    ),
    "design": "ui ux designer user research prototyping figma visual design",
    "ops": "devops platform engineering ci cd terraform kubernetes cloud infrastructure operations",
    "finance": "finance analyst banking accounting audit risk regulatory reporting",
    "marketing": "marketing seo social media campaign content growth",
}

SENIORITY_TEMPLATES: Final[dict[SeniorityLevel, str]] = {
    "intern": "intern trainee student learning first experience",
    "junior": "junior associate early career contributes with guidance",
    "mid": "independent engineer delivers projects end to end",
    "senior": "senior engineer architect owns complex systems mentors",
    "lead": "lead principal head manager strategic technical leadership",
}

ROLE_SIGNAL_KEYWORDS: Final[dict[RoleCategory, tuple[str, ...]]] = {
    "software": (
        "software engineer",
        "developer",
        "backend",
        "frontend",
        "fullstack",
        "api",
        "python",
        "java",
        "javascript",
        "typescript",
    ),
    "data": (
        "data architect",
        "data engineer",
        "data platform",
        "data warehouse",
        "etl",
        "elt",
        "snowflake",
        "databricks",
        "spark",
        "analytics engineer",
        "dbt",
        "sql",
    ),
    "management": (
        "management",
        "manager",
        "leadership",
        "stakeholder",
        "people management",
        "team lead",
        "head of",
        "director",
        "roadmap",
        "delivery manager",
    ),
    "ops": (
        "devops",
        "platform engineer",
        "ci/cd",
        "terraform",
        "kubernetes",
        "operations",
        "site reliability",
    ),
    "finance": ("finance", "banking", "risk", "accounting", "audit", "treasury"),
    "marketing": ("marketing", "seo", "campaign", "social media", "brand"),
    "design": ("ux", "ui", "figma", "designer", "graphic design"),
    "logistics": ("logistics", "supply chain", "warehouse"),
    "food_service": ("restaurant", "barista", "kitchen", "waiter", "hospitality"),
}

SENIORITY_SIGNAL_KEYWORDS: Final[dict[SeniorityLevel, tuple[str, ...]]] = {
    "intern": ("intern", "trainee", "student"),
    "junior": ("junior", "associate"),
    "mid": ("engineer", "specialist", "consultant"),
    "senior": ("senior", "lead engineer", "architect"),
    "lead": ("lead", "principal", "head", "manager", "director"),
}


class ContactInfo(TypedDict):
    email: str | None
    phone: str | None


class ExperienceEntry(TypedDict):
    title: str
    start_year: int
    end_year: int
    years: float
    range_text: str


class NormalizedCV(TypedDict):
    contact: ContactInfo
    experience_entries: list[ExperienceEntry]
    experience_years: float
    experience_confidence: ConfidenceLevel
    skills: list[str]
    education: EducationLevel
    role_signals: dict[str, int]
    seniority_signals: dict[str, int]
    strongest_role_signal: str
    strongest_seniority_signal: str
    parser_confidence: ConfidenceLevel
    warnings: list[str]


class ParsedCV(TypedDict):
    email: str | None
    phone: str | None
    raw_text: str
    raw_text_length: int
    normalized: NormalizedCV


class EnrichedCV(ParsedCV):
    role_category: str
    role_category_secondary: str
    role_scores: dict[str, float]
    seniority: SeniorityLevel
    seniority_scores: dict[str, float]
    seniority_combined: dict[str, float]
    jobs: list[ExperienceEntry]
    total_exp_score: float
    years_experience: float
    skills: list[str]
    education: EducationLevel
    parser_confidence: ConfidenceLevel
    parser_warnings: list[str]


class JobProfile(TypedDict):
    job_title: str
    seniority: SeniorityLevel
    years_required: int
    skills: list[str]
    education: EducationLevel
    role_category: JobRoleCategory


class ScoreBreakdown(TypedDict):
    skills: float
    seniority: float
    experience: float
    role: float
    education: float


class MatchResult(TypedDict):
    final_score: float
    breakdown: ScoreBreakdown
    parser_confidence: ConfidenceLevel
    parser_warnings: list[str]
    cv: EnrichedCV
    job: JobProfile
    explanation: NotRequired[str]
