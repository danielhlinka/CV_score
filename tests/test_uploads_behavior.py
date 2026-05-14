import io
import tempfile
import unittest
from pathlib import Path
from uuid import UUID
from unittest.mock import patch

from werkzeug.datastructures import FileStorage
from werkzeug.exceptions import BadRequest, InternalServerError, UnsupportedMediaType

from web.uploads import UploadLifecycle


class UploadLifecycleTests(unittest.TestCase):
    def _make_uploader(self, upload_dir: str) -> UploadLifecycle:
        return UploadLifecycle(Path(upload_dir), {".pdf", ".docx"})

    def test_validate_keeps_existing_error_messages(self):
        with tempfile.TemporaryDirectory() as upload_dir:
            uploader = self._make_uploader(upload_dir)

            with self.assertRaises(BadRequest) as missing:
                uploader.validate(None)
            self.assertEqual(missing.exception.description, "Missing uploaded file in field 'cv'.")

            with self.assertRaises(BadRequest) as empty_name:
                uploader.validate(FileStorage(stream=io.BytesIO(b""), filename=""))
            self.assertEqual(empty_name.exception.description, "No CV file selected.")

            with self.assertRaises(BadRequest) as invalid_name:
                uploader.validate(FileStorage(stream=io.BytesIO(b""), filename="////"))
            self.assertEqual(invalid_name.exception.description, "Invalid CV filename.")

            with self.assertRaises(UnsupportedMediaType) as unsupported:
                uploader.validate(FileStorage(stream=io.BytesIO(b""), filename="cv.txt"))
            self.assertEqual(
                unsupported.exception.description,
                "Unsupported file type. Allowed: .docx, .pdf.",
            )

            validated = uploader.validate(FileStorage(stream=io.BytesIO(b""), filename="cv.PDF"))
            self.assertEqual(validated.safe_name, "cv.PDF")

    def test_build_unique_path_uses_folder_and_normalizes_suffix(self):
        with tempfile.TemporaryDirectory() as upload_dir:
            uploader = self._make_uploader(upload_dir)
            with patch("web.uploads.uuid.uuid4", return_value=UUID("12345678-1234-5678-1234-567812345678")):
                staged_path = uploader.build_unique_path("Candidate.PDF")

            self.assertEqual(staged_path.parent, Path(upload_dir))
            self.assertEqual(staged_path.name, "Candidate-12345678.pdf")

    def test_stage_cleans_up_file_on_success_and_failure_paths(self):
        with tempfile.TemporaryDirectory() as upload_dir:
            uploader = self._make_uploader(upload_dir)
            storage_success = FileStorage(stream=io.BytesIO(b"%PDF-1.4"), filename="cv.pdf")

            with uploader.stage(storage_success) as staged:
                self.assertTrue(staged.path.exists())
                self.assertEqual(staged.path.suffix, ".pdf")

            self.assertFalse(staged.path.exists())

            storage_failure = FileStorage(stream=io.BytesIO(b"%PDF-1.4"), filename="cv.pdf")
            staged_path: Path | None = None

            with self.assertRaises(RuntimeError):
                with uploader.stage(storage_failure) as staged_on_error:
                    staged_path = staged_on_error.path
                    self.assertTrue(staged_on_error.path.exists())
                    raise RuntimeError("boom")

            self.assertIsNotNone(staged_path)
            self.assertFalse(staged_path.exists())

    def test_stage_wraps_save_oserror_with_compatible_http_error(self):
        with tempfile.TemporaryDirectory() as upload_dir:
            uploader = self._make_uploader(upload_dir)
            storage = FileStorage(stream=io.BytesIO(b"content"), filename="cv.pdf")

            def _partial_write_then_fail(destination):
                Path(destination).write_bytes(b"partial")
                raise OSError("disk full")

            with patch.object(storage, "save", side_effect=_partial_write_then_fail):
                with self.assertRaises(InternalServerError) as err:
                    with uploader.stage(storage):
                        self.fail("stage should not yield when save fails")

            self.assertEqual(err.exception.description, "Unable to store uploaded CV for processing.")
            self.assertEqual(list(Path(upload_dir).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
