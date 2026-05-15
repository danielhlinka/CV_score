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
    """Represents a request file that passed input validation checks.
    Stores sanitized filename and original file-storage handle."""
    file_storage: FileStorage
    safe_name: str


@dataclass(frozen=True, slots=True)
class StagedUpload:
    """Represents a temporary file staged for downstream CV processing.
    Carries safe original name and generated on-disk path."""
    safe_name: str
    path: Path


class UploadLifecycle:
    """Handle CV upload validation, staging, and deterministic cleanup.
    Encapsulates file safety checks and temporary-file lifecycle rules."""

    def __init__(self, upload_folder: Path, allowed_extensions: Iterable[str]) -> None:
        """Initialize upload storage and normalize allowed file extensions.
        Fails fast when extension configuration is empty."""
        normalized_extensions = {suffix.lower() for suffix in allowed_extensions}
        if not normalized_extensions:
            raise ValueError("allowed_extensions must not be empty.")

        self._upload_folder = Path(upload_folder)
        self._allowed_extensions = frozenset(normalized_extensions)
        self._upload_folder.mkdir(parents=True, exist_ok=True)

    @property
    def allowed_extensions(self) -> frozenset[str]:
        """Expose immutable extension allow-list for diagnostics and tests.
        Keeps upload policy readable without exposing mutable internals."""
        return self._allowed_extensions

    def validate(self, file_storage: FileStorage | None) -> ValidatedUpload:
        """Validate presence, filename, and extension for uploaded CV file.
        Returns sanitized upload metadata used by staging operations."""
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
        """Create a collision-resistant temporary file path for staging.
        Preserves extension while adding a short UUID suffix."""
        stem = Path(safe_name).stem
        suffix = Path(safe_name).suffix.lower()
        unique_name = f"{stem}-{uuid.uuid4().hex[:8]}{suffix}"
        return self._upload_folder / unique_name

    def _cleanup(self, staged_path: Path) -> None:
        """Best-effort removal of staged files after processing completes.
        Logs failures but never raises from cleanup paths."""
        try:
            staged_path.unlink(missing_ok=True)
        except OSError:
            logger.warning("Failed to remove temporary uploaded CV: %s", staged_path)

    @contextmanager
    def stage(self, file_storage: FileStorage | None) -> Iterator[StagedUpload]:
        """Context manager that validates, stores, and later removes upload.
        Guarantees cleanup on both success and error paths."""
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
