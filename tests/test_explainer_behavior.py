import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from pipeline import explainer


def _sample_result() -> dict:
    return {
        "cv": {
            "seniority": "senior",
            "years_experience": 6.7,
            "skills": ["python", "spark"],
            "education": "master",
            "role_category": "data",
        },
        "job": {
            "job_title": "Data Architect",
            "seniority": "senior",
            "years_required": 5,
            "skills": ["python", "spark", "snowflake"],
            "education": "bachelor",
        },
        "breakdown": {
            "skills": 0.8,
            "seniority": 0.9,
            "experience": 1.0,
            "education": 1.0,
        },
        "final_score": 0.9,
    }


def _response_with_text(content: str):
    message = SimpleNamespace(content=content)
    choice = SimpleNamespace(message=message)
    return SimpleNamespace(choices=[choice])


class _ClientWithCreate:
    def __init__(self, create_callback):
        completions = SimpleNamespace(create=create_callback)
        self.chat = SimpleNamespace(completions=completions)


class ExplainerBehaviorTests(unittest.TestCase):
    def test_missing_openai_api_key_returns_existing_message(self):
        instance = explainer.OpenAIExplainer(
            client_factory=lambda _api_key: self.fail("client factory should not run without API key")
        )

        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            output = instance.explain(_sample_result())

        self.assertEqual(output, "⚠️ Could not generate explanation: OPENAI_API_KEY is missing.")

    def test_api_error_returns_existing_generic_message(self):
        def _raise_error(**_kwargs):
            raise RuntimeError("boom")

        instance = explainer.OpenAIExplainer(client_factory=lambda _api_key: _ClientWithCreate(_raise_error))

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            output = instance.explain(_sample_result())

        self.assertEqual(
            output,
            "⚠️ Could not generate explanation right now. Please try again later.",
        )

    def test_empty_response_content_returns_existing_generic_message(self):
        instance = explainer.OpenAIExplainer(
            client_factory=lambda _api_key: _ClientWithCreate(lambda **_kwargs: _response_with_text(""))
        )

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            output = instance.explain(_sample_result())

        self.assertEqual(
            output,
            "⚠️ Could not generate explanation right now. Please try again later.",
        )

    def test_successful_response_returns_generated_content(self):
        calls: list[dict] = []

        def _create(**kwargs):
            calls.append(kwargs)
            return _response_with_text("Generated markdown explanation")

        instance = explainer.OpenAIExplainer(
            model="gpt-4o-mini",
            max_tokens=1000,
            client_factory=lambda _api_key: _ClientWithCreate(_create),
        )

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            output = instance.explain(_sample_result())

        self.assertEqual(output, "Generated markdown explanation")
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["model"], "gpt-4o-mini")
        self.assertEqual(calls[0]["max_tokens"], 1000)
        self.assertEqual(calls[0]["messages"][0]["role"], "user")
        self.assertIn("CANDIDATE:", calls[0]["messages"][0]["content"])

    def test_public_explain_function_keeps_compatibility(self):
        with patch.object(explainer, "DEFAULT_EXPLAINER") as default_explainer:
            default_explainer.explain.return_value = "ok"
            output = explainer.explain(_sample_result())

        self.assertEqual(output, "ok")

    def test_missing_expected_result_keys_still_raises_key_error(self):
        instance = explainer.OpenAIExplainer(client_factory=lambda _api_key: _ClientWithCreate(lambda **_k: None))

        with self.assertRaises(KeyError):
            instance.explain({})


if __name__ == "__main__":
    unittest.main()
