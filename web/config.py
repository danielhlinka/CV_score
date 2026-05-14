import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_MAX_UPLOAD_MB = 10
TRUTHY_ENV_VALUES = {"1", "true", "yes", "on"}


def read_max_upload_bytes() -> int:
    raw_mb = os.getenv("MAX_UPLOAD_MB", str(DEFAULT_MAX_UPLOAD_MB)).strip()
    try:
        max_mb = int(raw_mb)
    except ValueError:
        logger.warning(
            "Invalid MAX_UPLOAD_MB='%s'. Falling back to %d MB.",
            raw_mb,
            DEFAULT_MAX_UPLOAD_MB,
        )
        max_mb = DEFAULT_MAX_UPLOAD_MB

    if max_mb <= 0:
        logger.warning(
            "Non-positive MAX_UPLOAD_MB='%s'. Falling back to %d MB.",
            raw_mb,
            DEFAULT_MAX_UPLOAD_MB,
        )
        max_mb = DEFAULT_MAX_UPLOAD_MB

    return max_mb * 1024 * 1024


def read_debug_mode() -> bool:
    return os.getenv("FLASK_DEBUG", "").strip().lower() in TRUTHY_ENV_VALUES


def resolve_upload_folder(base_dir: Path) -> Path:
    raw_upload_folder = os.getenv("UPLOAD_FOLDER", "upload").strip() or "upload"
    upload_folder = Path(raw_upload_folder)
    if not upload_folder.is_absolute():
        upload_folder = base_dir / upload_folder

    upload_folder.mkdir(parents=True, exist_ok=True)
    return upload_folder


def runtime_config(base_dir: Path) -> dict[str, Any]:
    return {
        "BASE_DIR": base_dir,
        "UPLOAD_FOLDER": resolve_upload_folder(base_dir),
        "MAX_CONTENT_LENGTH": read_max_upload_bytes(),
        "RUN_DEBUG": read_debug_mode(),
    }
