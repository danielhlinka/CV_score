import logging
import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
DEFAULT_ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
logger = logging.getLogger(__name__)

def explain(result: dict) -> str:
    cv = result["cv"]
    job = result["job"]
    breakdown = result["breakdown"]

    prompt = f"""
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

    try:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return "⚠️ Could not generate explanation: ANTHROPIC_API_KEY is missing."

        client = Anthropic(api_key=api_key)
        response = client.messages.create(
            model=DEFAULT_ANTHROPIC_MODEL,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )

        parts = [
            block.text for block in response.content
            if getattr(block, "type", None) == "text" and getattr(block, "text", "")
        ]
        if not parts:
            return "⚠️ Could not generate explanation: empty response from Anthropic."
        return "\n".join(parts)
    except Exception:
        logger.exception("Could not generate explanation from Anthropic.")
        return "⚠️ Could not generate explanation right now. Please try again later."
