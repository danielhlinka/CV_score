from __future__ import annotations

import re

SKILL_GROUPS = {
    "leadership": ["leadership", "lead", "led"],
    "people management": ["people management", "team management", "team lead", "managed"],
    "mentoring": ["mentoring", "mentored"],
    "stakeholder management": ["stakeholder", "stakeholders"],
    "strategic planning": ["strategic planning", "strategy"],
    "spark": ["spark", "apache spark", "pyspark", "databricks", "delta live tables", "delta lake"],
    "snowflake": ["snowflake"],
    "cloud": ["cloud", "multi-cloud", "multicloud", "azure", "aws", "gcp", "google cloud"],
    "architecture": ["architecture", "architect", "solution architect", "data architect", "enterprise architecture"],
}

KNOWN_SKILLS = [
    "python",
    "java",
    "php",
    "html",
    "css",
    "javascript",
    "c",
    "c++",
    "c#",
    "sql",
    "postgresql",
    "mysql",
    "mongodb",
    "flask",
    "django",
    "react",
    "docker",
    "git",
    "linux",
    "blender",
    "3d modeling",
    "animation",
    "microsoft word",
    "excel",
    "powerpoint",
    "typescript",
    "node",
    "aws",
    "azure",
    "gcp",
    "terraform",
    "ci/cd",
    "rag",
    "langchain",
    "langgraph",
    "hiring",
    "budget",
    "p&l",
    "cross-functional",
    "roadmap",
    "okr",
    "product management",
    "project management",
    "risk management",
    "agile",
    "scrum",
    "kanban",
    "sprint",
    "delivery",
]


def extract_skills(text: str) -> list[str]:
    """Extract canonical skills from CV text using variant dictionaries.
    Deduplicates while preserving first-seen ordering for readability."""
    text_lower = text.lower()
    found: list[str] = []
    seen: set[str] = set()

    for canonical, variants in SKILL_GROUPS.items():
        for variant in variants:
            if re.search(rf"\b{re.escape(variant)}\b", text_lower):
                found.append(canonical)
                seen.add(canonical)
                break

    for skill in KNOWN_SKILLS:
        if re.search(rf"\b{re.escape(skill)}\b", text_lower):
            if skill not in seen:
                found.append(skill)
                seen.add(skill)

    return found
