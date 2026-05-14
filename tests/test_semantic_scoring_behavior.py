import unittest
from unittest.mock import patch

import numpy as np

import pipeline.embedder as embedder_module
from pipeline import ROLE_TEMPLATES, SENIORITY_TEMPLATES
from pipeline.embedder import enrich_cv
from pipeline.matcher import _experience_score, _skills_score


class SemanticScoringBehaviorTests(unittest.TestCase):
    def test_parser_confidence_guardrails_for_skills_and_experience(self):
        job = {
            "job_title": "Data Engineer",
            "seniority": "mid",
            "years_required": 4,
            "skills": ["python", "spark"],
            "education": "bachelor",
            "role_category": "data",
        }

        cv_low = {"skills": [], "parser_confidence": "low", "years_experience": 0}
        cv_medium = {"skills": [], "parser_confidence": "medium", "years_experience": 0}
        cv_high = {"skills": [], "parser_confidence": "high", "years_experience": 0}

        self.assertEqual(_skills_score(cv_low, job), 0.5)
        self.assertEqual(_skills_score(cv_medium, job), 0.0)
        self.assertEqual(_skills_score(cv_high, job), 0.0)

        self.assertEqual(_experience_score(cv_low, job), 0.45)
        self.assertEqual(_experience_score(cv_medium, job), 0.25)
        self.assertEqual(_experience_score(cv_high, job), 0.0)

    def test_skills_score_blends_exact_and_semantic_similarity(self):
        job = {
            "job_title": "Data Engineer",
            "seniority": "mid",
            "years_required": 2,
            "skills": ["python", "spark"],
            "education": "bachelor",
            "role_category": "data",
        }
        cv = {"skills": ["python", "sql"], "parser_confidence": "high", "years_experience": 4}

        vectors = {
            "python": np.array([1.0, 0.0]),
            "spark": np.array([1.0, 0.0]),
            "sql": np.array([0.0, 1.0]),
        }

        with patch("pipeline.matcher.memoized_embedding", side_effect=lambda text: vectors[text]):
            self.assertEqual(_skills_score(cv, job), 0.75)

    @patch("pipeline.embedder.experience_score", return_value=0.88)
    @patch("pipeline.embedder.combined_seniority", return_value=("mid", {"mid": 0.9}))
    def test_embedder_template_cache_and_output_schema_stay_stable(
        self,
        _combined_seniority,
        _experience_score,
    ):
        embedder_module._get_role_template_embeddings.cache_clear()
        embedder_module._get_seniority_template_embeddings.cache_clear()

        def fake_embedding(text: str) -> np.ndarray:
            seed = sum(ord(ch) for ch in text)
            return np.array(
                [
                    float((seed % 17) + 1),
                    float((seed % 13) + 1),
                    float((seed % 11) + 1),
                ],
            )

        parsed = {
            "email": "a@b.com",
            "phone": "+420000000000",
            "raw_text": "sample",
            "raw_text_length": 6,
            "normalized": {
                "contact": {"email": "a@b.com", "phone": "+420000000000"},
                "experience_entries": [{"title": "Data Engineer", "start_year": 2020, "end_year": 2024, "years": 4.0, "range_text": "2020-2024"}],
                "experience_years": 4.0,
                "experience_confidence": "high",
                "skills": ["python", "spark", "sql"],
                "education": "bachelor",
                "role_signals": {"data": 3},
                "seniority_signals": {"mid": 2},
                "strongest_role_signal": "data engineer",
                "strongest_seniority_signal": "mid",
                "parser_confidence": "high",
                "warnings": ["w1"],
            },
        }

        with patch("pipeline.embedder.memoized_embedding", side_effect=fake_embedding) as mocked_embedding:
            result_one = enrich_cv(parsed)
            result_two = enrich_cv(parsed)

        calls = [call.args[0] for call in mocked_embedding.call_args_list]
        role_template_calls = [text for text in calls if text in ROLE_TEMPLATES.values()]
        seniority_template_calls = [text for text in calls if text in SENIORITY_TEMPLATES.values()]

        self.assertEqual(len(role_template_calls), len(ROLE_TEMPLATES))
        self.assertEqual(len(seniority_template_calls), len(SENIORITY_TEMPLATES))
        self.assertEqual(result_one["parser_confidence"], "high")
        self.assertEqual(result_one["parser_warnings"], ["w1"])
        self.assertIn("role_scores", result_one)
        self.assertIn("seniority_scores", result_one)
        self.assertEqual(result_one["role_category"], result_two["role_category"])
        self.assertEqual(result_one["seniority"], result_two["seniority"])


if __name__ == "__main__":
    unittest.main()
