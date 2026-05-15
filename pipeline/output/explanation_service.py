from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Callable, Mapping

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
DEFAULT_OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MISSING_API_KEY_MESSAGE = "⚠️ Could not generate explanation: OPENAI_API_KEY is missing."
GENERIC_FAILURE_MESSAGE = "⚠️ Could not generate explanation right now. Please try again later."
logger = logging.getLogger(__name__)

ClientFactory = Callable[[str], Any]


def _build_openai_client(api_key: str) -> OpenAI:
    """Construct an OpenAI client scoped to the provided API key.
    Isolated factory keeps explainer dependency injection testable."""
    return OpenAI(api_key=api_key)


def _build_prompt(result: Mapping[str, Any]) -> str:
    """Create the structured LLM prompt from scored CV/job payload data.
    Enforces a stable output template for downstream rendering."""
    cv = result["cv"]
    job = result["job"]
    breakdown = result["breakdown"]
    return f"""
You are an expert HR analyst. Write a concise, well-structured report in English using Markdown.
Be specific, no generic advice. Use emoji for readability.

CANDIDATE:
- Seniority: {cv.get("seniority")}
- Years of experience: {cv.get("years_experience")}
- Skills: {", ".join(cv.get("skills", []))}
- Education: {cv.get("education")}
- Role category: {cv.get("role_category")}

JOB REQUIREMENTS:
- Title: {job.get("job_title")}
- Seniority: {job.get("seniority")}
- Years required: {job.get("years_required")}
- Required skills: {", ".join(job.get("skills", []))}
- Education: {job.get("education")}

SCORE BREAKDOWN:
- Skills: {breakdown.get("skills", 0) * 100:.1f}%
- Seniority: {breakdown.get("seniority", 0) * 100:.1f}%
- Experience: {breakdown.get("experience", 0) * 100:.1f}%
- Education: {breakdown.get("education", 0) * 100:.1f}%
- Final score: {result.get("final_score", 0) * 100:.1f}%

Use exactly this format:

## 🎯 Why this score?
2–3 sentences.

## 💪 Strengths
- bullet points

## ⚠️ Weaknesses
- bullet points

## 🚀 How to reach +30% higher salary?
- specific steps only

## 💶 Salary Estimate (SK/CZ market, monthly gross)
| | Range |
|---|---|
| **Current** | €X,XXX – €X,XXX / month |
| **Potential** | €X,XXX – €X,XXX / month |
"""


def _extract_response_content(response: Any) -> str:
    """Extract plain message content from OpenAI chat completion payload.
    Returns empty string when response shape is missing expected fields."""
    choices = getattr(response, "choices", None)
    if not choices:
        return ""
    message = getattr(choices[0], "message", None)
    return getattr(message, "content", "") or ""


@dataclass(frozen=True, slots=True)
class OpenAIExplainer:
    model: str = DEFAULT_OPENAI_MODEL
    api_key_env_var: str = "OPENAI_API_KEY"
    max_tokens: int = 1000
    client_factory: ClientFactory = _build_openai_client

    def explain(self, result: dict) -> str:
        """Generate a natural-language explanation for a scoring result.
        Falls back to safe messages on missing key or API/runtime failures."""
        prompt = _build_prompt(result)
        api_key = os.getenv(self.api_key_env_var)
        if not api_key:
            return MISSING_API_KEY_MESSAGE

        try:
            client = self.client_factory(api_key)
            response = client.chat.completions.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception:
            logger.exception("Could not generate explanation from OpenAI.")
            return GENERIC_FAILURE_MESSAGE

        content = _extract_response_content(response)
        if not content:
            return GENERIC_FAILURE_MESSAGE
        return content


DEFAULT_EXPLAINER = OpenAIExplainer()


def explain(result: dict) -> str:
    """Module-level compatibility wrapper for the default explainer.
    Preserves stable `explain(result)` import path across refactors."""
    return DEFAULT_EXPLAINER.explain(result)
