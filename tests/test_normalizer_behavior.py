import unittest

from pipeline.lib.normalizer import normalize_cv_text


class NormalizerBehaviorTests(unittest.TestCase):
    def test_education_ranges_are_excluded_from_experience(self):
        text = (
            "Data Engineer\n"
            "01/2020 - 01/2022\n"
            "Aarhus University\n"
            "09/2015 - 06/2018\n"
        )

        normalized = normalize_cv_text(text)

        self.assertEqual(len(normalized["experience_entries"]), 1)
        self.assertEqual(normalized["experience_entries"][0]["range_text"], "01/2020 - 01/2022")
        self.assertEqual(normalized["experience_years"], 2.08)
        self.assertIn(
            "Skipped 1 education-related date range(s) while computing work experience.",
            normalized["warnings"],
        )

    def test_parser_confidence_falls_back_when_skills_are_sparse(self):
        text = (
            "Data Engineer\n"
            "01/2020 - 01/2021\n"
            "Analytics Engineer\n"
            "02/2021 - 02/2022\n"
            "Python\n"
        )

        normalized = normalize_cv_text(text)

        self.assertEqual(normalized["experience_confidence"], "high")
        self.assertEqual(normalized["parser_confidence"], "medium")
        self.assertEqual(len(normalized["experience_entries"]), 2)

    def test_warnings_shape_for_sparse_text(self):
        normalized = normalize_cv_text("Lorem ipsum dolor sit amet.")

        self.assertListEqual(
            normalized["warnings"],
            [
                "No experience date ranges detected from full CV text.",
                "No skills detected from CV text.",
                "No education level confidently detected.",
            ],
        )
        self.assertTrue(all(isinstance(item, str) for item in normalized["warnings"]))


if __name__ == "__main__":
    unittest.main()
