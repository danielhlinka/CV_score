from __future__ import annotations

from typing import Final, Literal

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
