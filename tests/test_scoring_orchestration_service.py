import unittest

from web.scoring_service import ScoringOrchestrationService


class ScoringOrchestrationServiceTests(unittest.TestCase):
    def test_score_runs_pipeline_steps_in_expected_order(self):
        call_order: list[str] = []

        job_profile = {
            "job_title": "Data Architect",
            "seniority": "mid",
            "years_required": 5,
            "skills": ["python", "spark"],
            "education": "bachelor",
            "role_category": "data",
        }
        parsed_cv = {
            "email": None,
            "phone": None,
            "raw_text": "raw cv text",
            "raw_text_length": 11,
            "normalized": {
                "contact": {"email": None, "phone": None},
                "experience_entries": [],
                "experience_years": 0.0,
                "experience_confidence": "low",
                "skills": [],
                "education": "none",
                "role_signals": {},
                "seniority_signals": {},
                "strongest_role_signal": "",
                "strongest_seniority_signal": "",
                "parser_confidence": "low",
                "warnings": [],
            },
        }
        enriched_cv = {
            **parsed_cv,
            "role_category": "data",
            "role_category_secondary": "software",
            "role_scores": {"data": 1.0},
            "seniority": "mid",
            "seniority_scores": {"mid": 1.0},
            "seniority_combined": {"mid": 1.0},
            "jobs": [],
            "total_exp_score": 0.0,
            "years_experience": 0.0,
            "skills": [],
            "education": "none",
            "parser_confidence": "low",
            "parser_warnings": [],
        }
        match_result = {
            "final_score": 0.8,
            "breakdown": {
                "skills": 0.8,
                "seniority": 0.8,
                "experience": 0.8,
                "role": 0.8,
                "education": 0.8,
            },
            "parser_confidence": "low",
            "parser_warnings": [],
            "cv": enriched_cv,
            "job": job_profile,
        }

        def parse_job(form):
            call_order.append("parse_job")
            self.assertEqual(form["job_title"], "Data Architect")
            return job_profile

        def extract_text(path: str) -> str:
            call_order.append("extract_text")
            self.assertEqual(path, "/tmp/cv.pdf")
            return "raw cv text"

        def parse_cv(raw_text: str):
            call_order.append("parse_cv")
            self.assertEqual(raw_text, "raw cv text")
            return parsed_cv

        def enrich_cv(parsed):
            call_order.append("enrich_cv")
            self.assertIs(parsed, parsed_cv)
            return enriched_cv

        def match(cv, job):
            call_order.append("match")
            self.assertIs(cv, enriched_cv)
            self.assertIs(job, job_profile)
            return match_result

        def sanity_check(result):
            call_order.append("sanity_check")
            self.assertIs(result, match_result)

        def explain(result):
            call_order.append("explain")
            self.assertIs(result, match_result)
            return "explanation text"

        service = ScoringOrchestrationService(
            parse_job=parse_job,
            extract_text=extract_text,
            parse_cv=parse_cv,
            enrich_cv=enrich_cv,
            match=match,
            sanity_check=sanity_check,
            explain=explain,
        )

        result = service.score(form={"job_title": "Data Architect"}, cv_path="/tmp/cv.pdf")

        self.assertEqual(
            call_order,
            [
                "parse_job",
                "extract_text",
                "parse_cv",
                "enrich_cv",
                "match",
                "sanity_check",
                "explain",
            ],
        )
        self.assertIs(result, match_result)
        self.assertEqual(result["explanation"], "explanation text")

    def test_score_preserves_match_contract_and_overwrites_explanation(self):
        result_from_match = {
            "final_score": 0.55,
            "breakdown": {
                "skills": 0.6,
                "seniority": 0.6,
                "experience": 0.6,
                "role": 0.2,
                "education": 0.8,
            },
            "parser_confidence": "medium",
            "parser_warnings": ["warn"],
            "cv": {"years_experience": 4.0},
            "job": {"job_title": "Data Engineer"},
            "explanation": "stale explanation",
        }

        service = ScoringOrchestrationService(
            parse_job=lambda form: {"job_title": form["job_title"]},
            extract_text=lambda path: "text",
            parse_cv=lambda raw_text: {"normalized": {}},
            enrich_cv=lambda parsed: {"normalized": {}},
            match=lambda cv, job: result_from_match,
            sanity_check=lambda result: None,
            explain=lambda result: "fresh explanation",
        )

        result = service.score(form={"job_title": "Data Engineer"}, cv_path="/tmp/cv.pdf")

        self.assertIs(result, result_from_match)
        self.assertEqual(
            set(result.keys()),
            {
                "final_score",
                "breakdown",
                "parser_confidence",
                "parser_warnings",
                "cv",
                "job",
                "explanation",
            },
        )
        self.assertEqual(result["explanation"], "fresh explanation")
        self.assertEqual(result["final_score"], 0.55)
        self.assertEqual(result["parser_confidence"], "medium")
        self.assertEqual(result["parser_warnings"], ["warn"])


if __name__ == "__main__":
    unittest.main()
