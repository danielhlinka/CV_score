import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from werkzeug.exceptions import BadRequest

from app import create_app
from pipeline.lib.extractor import extract_skills
from pipeline.lib.job_parser import parse_job


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

    def test_index_route_returns_ok(self):
        flask_app = create_app({"TESTING": True})
        client = flask_app.test_client()

        response = client.get("/")

        self.assertEqual(response.status_code, 200)

    def test_score_missing_file_returns_bad_request_json(self):
        flask_app = create_app({"TESTING": True})
        client = flask_app.test_client()

        response = client.post(
            "/score",
            data={"job_title": "Data Architect"},
            headers={"Accept": "application/json"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(), {"error": "Missing uploaded file in field 'cv'."})

    def test_score_unsupported_extension_returns_415_json(self):
        flask_app = create_app({"TESTING": True})
        client = flask_app.test_client()

        response = client.post(
            "/score",
            data={
                "job_title": "Data Architect",
                "cv": (io.BytesIO(b"not a pdf"), "cv.txt"),
            },
            content_type="multipart/form-data",
            headers={"Accept": "application/json"},
        )

        self.assertEqual(response.status_code, 415)
        error = response.get_json()["error"]
        self.assertIn("Unsupported file type.", error)
        self.assertIn(".pdf", error)
        self.assertIn(".docx", error)

    @patch("web.routes.render_template", return_value="ok")
    @patch("web.routes.get_scoring_service")
    def test_score_deletes_uploaded_temp_file_after_success(
        self,
        mocked_get_scoring_service,
        _render_template,
    ):
        score_service = MagicMock()
        score_service.score.return_value = {
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
            "explanation": "ok",
        }
        mocked_get_scoring_service.return_value = score_service

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
            _render_template.assert_called_once()
            self.assertEqual(_render_template.call_args.args[0], "results.html")
            score_service.score.assert_called_once()
            called_cv_path = score_service.score.call_args.kwargs["cv_path"]
            self.assertIsInstance(called_cv_path, str)
            self.assertFalse(Path(called_cv_path).exists())

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
