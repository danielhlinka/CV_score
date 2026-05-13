import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from werkzeug.exceptions import BadRequest

from app import create_app
from pipeline.extractor import extract_skills
from pipeline.job_parser import parse_job


class CoreBehaviorTests(unittest.TestCase):
    def test_parse_job_rejects_non_numeric_years_required(self):
        form = {
            "job_title": "Data Architect",
            "seniority": "junior",
            "years_required": "abc",
            "skills": "python,sql",
            "education": "bachelor",
            "role_category": "data",
        }

        with self.assertRaises(BadRequest) as ctx:
            parse_job(form)

        self.assertIn("must be a whole number", ctx.exception.description)

    @patch("app.render_template", return_value="ok")
    @patch("app.explain", return_value="ok")
    @patch("app.sanity_check", return_value=None)
    @patch(
        "app.match",
        return_value={
            "final_score": 1.0,
            "breakdown": {
                "skills": 1.0,
                "seniority": 1.0,
                "experience": 1.0,
                "role": 1.0,
                "education": 1.0,
            },
            "parser_confidence": "high",
            "parser_warnings": [],
            "cv": {},
            "job": {},
        },
    )
    @patch("app.enrich_cv", side_effect=lambda cv: cv)
    @patch("app.parse_cv", return_value={})
    @patch("app.extract_text", return_value="cv text")
    def test_score_deletes_uploaded_temp_file_after_success(
        self,
        _extract_text,
        _parse_cv,
        _enrich_cv,
        _match,
        _sanity_check,
        _explain,
        _render_template,
    ):
        with tempfile.TemporaryDirectory() as upload_dir:
            flask_app = create_app({"TESTING": True, "UPLOAD_FOLDER": upload_dir})
            client = flask_app.test_client()

            response = client.post(
                "/score",
                data={
                    "job_title": "Data Architect",
                    "seniority": "junior",
                    "years_required": "1",
                    "skills": "python,spark,snowflake",
                    "education": "bachelor",
                    "role_category": "data",
                    "cv": (io.BytesIO(b"%PDF-1.4 fake"), "cv.pdf"),
                },
                content_type="multipart/form-data",
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(list(Path(upload_dir).iterdir()), [])

    def test_extract_skills_canonicalizes_spark_and_keeps_snowflake(self):
        text = (
            "Snowflake (Advanced). "
            "Apache Spark / Databricks (PySpark, Delta, Delta Live Tables)."
        )

        skills = extract_skills(text)

        self.assertIn("spark", skills)
        self.assertEqual(skills.count("spark"), 1)
        self.assertIn("snowflake", skills)


if __name__ == "__main__":
    unittest.main()
