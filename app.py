import logging
import os
import uuid
from pathlib import Path
from typing import Any, Mapping

from flask import Flask, current_app, render_template, request
from werkzeug.datastructures import FileStorage
from werkzeug.exceptions import (
    BadRequest,
    HTTPException,
    InternalServerError,
    RequestEntityTooLarge,
    UnprocessableEntity,
    UnsupportedMediaType,
)
from werkzeug.utils import secure_filename

from pipeline.embedder import enrich_cv
from pipeline.explainer import explain
from pipeline.extractor import SUPPORTED_EXTENSIONS, extract_text
from pipeline.job_parser import parse_job
from pipeline.matcher import match
from pipeline.parser import parse_cv
from pipeline.sanity_check import sanity_check

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

DEFAULT_MAX_UPLOAD_MB = 10
TRUTHY_ENV_VALUES = {"1", "true", "yes", "on"}


def _read_max_upload_bytes() -> int:
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


def _read_debug_mode() -> bool:
    return os.getenv("FLASK_DEBUG", "").strip().lower() in TRUTHY_ENV_VALUES


def _resolve_upload_folder(base_dir: Path) -> Path:
    raw_upload_folder = os.getenv("UPLOAD_FOLDER", "upload").strip() or "upload"
    upload_folder = Path(raw_upload_folder)
    if not upload_folder.is_absolute():
        upload_folder = base_dir / upload_folder

    upload_folder.mkdir(parents=True, exist_ok=True)
    return upload_folder


def _runtime_config(base_dir: Path) -> dict[str, Any]:
    return {
        "BASE_DIR": base_dir,
        "UPLOAD_FOLDER": _resolve_upload_folder(base_dir),
        "MAX_CONTENT_LENGTH": _read_max_upload_bytes(),
        "RUN_DEBUG": _read_debug_mode(),
    }


def _validate_and_get_upload(file_storage: FileStorage | None) -> tuple[FileStorage, str]:
    if file_storage is None:
        raise BadRequest("Missing uploaded file in field 'cv'.")

    if not file_storage.filename:
        raise BadRequest("No CV file selected.")

    safe_name = secure_filename(file_storage.filename)
    if not safe_name:
        raise BadRequest("Invalid CV filename.")

    extension = Path(safe_name).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        allowed = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise UnsupportedMediaType(f"Unsupported file type. Allowed: {allowed}.")

    return file_storage, safe_name


def _build_upload_path(filename: str) -> Path:
    unique_name = f"{Path(filename).stem}-{uuid.uuid4().hex[:8]}{Path(filename).suffix.lower()}"
    upload_folder = Path(current_app.config["UPLOAD_FOLDER"])
    return upload_folder / unique_name


def _is_html_request() -> bool:
    accept = request.accept_mimetypes
    return accept["text/html"] >= accept["application/json"]


def _error_response(message: str, status_code: int):
    if _is_html_request():
        return render_template("index.html", error_message=message), status_code
    return {"error": message}, status_code


def create_app(test_config: Mapping[str, Any] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(_runtime_config(Path(__file__).resolve().parent))

    if test_config is not None:
        app.config.from_mapping(test_config)

    upload_folder = Path(app.config["UPLOAD_FOLDER"])
    upload_folder.mkdir(parents=True, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = upload_folder

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/score", methods=["POST"])
    def score():
        job_profile = parse_job(request.form)

        file_storage, safe_name = _validate_and_get_upload(request.files.get("cv"))
        save_path = _build_upload_path(safe_name)

        try:
            file_storage.save(save_path)
        except OSError as exc:
            logger.exception("Failed to save uploaded CV: %s", safe_name)
            raise InternalServerError("Unable to store uploaded CV for processing.") from exc

        try:
            raw_text = extract_text(str(save_path))
        except ValueError as exc:
            raise UnprocessableEntity(str(exc)) from exc
        except OSError as exc:
            logger.exception("Failed to read uploaded CV: %s", safe_name)
            raise InternalServerError("Failed to read uploaded CV.") from exc
        finally:
            try:
                save_path.unlink(missing_ok=True)
            except OSError:
                logger.warning("Failed to remove temporary uploaded CV: %s", save_path)

        cv_profile = parse_cv(raw_text)
        cv_profile = enrich_cv(cv_profile)

        result = match(cv_profile, job_profile)
        sanity_check(result)
        result["explanation"] = explain(result)

        return render_template("results.html", result=result)

    @app.errorhandler(RequestEntityTooLarge)
    def handle_request_too_large(exc: RequestEntityTooLarge):
        _ = exc
        max_mb = current_app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024)
        return _error_response(f"Uploaded file is too large. Maximum allowed size is {max_mb} MB.", 413)

    @app.errorhandler(BadRequest)
    def handle_bad_request(exc: BadRequest):
        return _error_response(exc.description or "Invalid request.", 400)

    @app.errorhandler(UnsupportedMediaType)
    def handle_unsupported_media_type(exc: UnsupportedMediaType):
        return _error_response(exc.description or "Unsupported media type.", 415)

    @app.errorhandler(UnprocessableEntity)
    def handle_unprocessable_entity(exc: UnprocessableEntity):
        return _error_response(exc.description or "Unable to process uploaded CV.", 422)

    @app.errorhandler(HTTPException)
    def handle_http_exception(exc: HTTPException):
        return _error_response(exc.description or "Request failed.", exc.code)

    @app.errorhandler(Exception)
    def handle_unexpected_error(exc: Exception):
        logger.exception("Unexpected server error", exc_info=exc)
        return _error_response("Internal server error.", 500)

    return app


app = create_app()


if __name__ == "__main__":
    debug_mode = bool(app.config.get("RUN_DEBUG", False))
    app.run(debug=debug_mode, use_reloader=debug_mode)
