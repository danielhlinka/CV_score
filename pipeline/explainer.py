import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Could not generate explanation: {e}"

