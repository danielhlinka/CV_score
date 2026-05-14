from __future__ import annotations

import logging
import uuid
from collections.abc import Iterable
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from werkzeug.datastructures import FileStorage
from werkzeug.exceptions import BadRequest, InternalServerError, UnsupportedMediaType
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ValidatedUpload:
    file_storage: FileStorage
    safe_name: str


@dataclass(frozen=True, slots=True)
class StagedUpload:
    safe_name: str
    path: Path


class UploadLifecycle:
    def __init__(self, upload_folder: Path, allowed_extensions: Iterable[str]) -> None:
        normalized_extensions = {suffix.lower() for suffix in allowed_extensions}
        if not normalized_extensions:
            raise ValueError("allowed_extensions must not be empty.")

        self._upload_folder = Path(upload_folder)
        self._allowed_extensions = frozenset(normalized_extensions)
        self._upload_folder.mkdir(parents=True, exist_ok=True)

    @property
    def allowed_extensions(self) -> frozenset[str]:
        return self._allowed_extensions

    def validate(self, file_storage: FileStorage | None) -> ValidatedUpload:
        if file_storage is None:
            raise BadRequest("Missing uploaded file in field 'cv'.")

        if not file_storage.filename:
            raise BadRequest("No CV file selected.")

        safe_name = secure_filename(file_storage.filename)
        if not safe_name:
            raise BadRequest("Invalid CV filename.")

        extension = Path(safe_name).suffix.lower()
        if extension not in self._allowed_extensions:
            allowed = ", ".join(sorted(self._allowed_extensions))
            raise UnsupportedMediaType(f"Unsupported file type. Allowed: {allowed}.")

        return ValidatedUpload(file_storage=file_storage, safe_name=safe_name)

    def build_unique_path(self, safe_name: str) -> Path:
        stem = Path(safe_name).stem
        suffix = Path(safe_name).suffix.lower()
        unique_name = f"{stem}-{uuid.uuid4().hex[:8]}{suffix}"
        return self._upload_folder / unique_name

    def _cleanup(self, staged_path: Path) -> None:
        try:
            staged_path.unlink(missing_ok=True)
        except OSError:
            logger.warning("Failed to remove temporary uploaded CV: %s", staged_path)

    @contextmanager
    def stage(self, file_storage: FileStorage | None) -> Iterator[StagedUpload]:
        validated = self.validate(file_storage)
        staged_path = self.build_unique_path(validated.safe_name)

        try:
            validated.file_storage.save(staged_path)
        except OSError as exc:
            self._cleanup(staged_path)
            logger.exception("Failed to save uploaded CV: %s", validated.safe_name)
            raise InternalServerError("Unable to store uploaded CV for processing.") from exc

        staged_upload = StagedUpload(safe_name=validated.safe_name, path=staged_path)
        try:
            yield staged_upload
        finally:
            self._cleanup(staged_path)
