import logging
from functools import lru_cache
from pathlib import Path

from flask import Blueprint, current_app, render_template, request
from werkzeug.exceptions import InternalServerError, UnprocessableEntity

from pipeline.extractor import SUPPORTED_EXTENSIONS
from web.scoring_service import ScoringOrchestrationService, build_scoring_orchestration_service
from web.uploads import UploadLifecycle

logger = logging.getLogger(__name__)

web_bp = Blueprint("web", __name__)


@lru_cache(maxsize=1)
def get_scoring_service() -> ScoringOrchestrationService:
    """Create and cache the scoring service for route-level reuse.
    Keeps dependency wiring stable across requests in a single process."""
    return build_scoring_orchestration_service()


def _build_uploader() -> UploadLifecycle:
    """Build an upload lifecycle helper using current runtime config.
    Restricts accepted CV formats to the supported extension set."""
    upload_folder = Path(current_app.config["UPLOAD_FOLDER"])
    return UploadLifecycle(upload_folder, SUPPORTED_EXTENSIONS)


@web_bp.route("/")
def index():
    """Render the main form used to submit CV and job requirements.
    Keeps GET behavior simple and side-effect free."""
    return render_template("index.html")


@web_bp.route("/score", methods=["POST"])
def score():
    """Validate and stage the uploaded CV, then execute the scoring flow.
    Maps domain/IO failures to consistent HTTP-level errors."""
    service = get_scoring_service()
    uploader = _build_uploader()

    with uploader.stage(request.files.get("cv")) as staged:
        try:
            result = service.score(form=request.form, cv_path=str(staged.path))
        except ValueError as exc:
            raise UnprocessableEntity(str(exc)) from exc
        except OSError as exc:
            logger.exception("Failed to read uploaded CV: %s", staged.safe_name)
            raise InternalServerError("Failed to read uploaded CV.") from exc

    return render_template("results.html", result=result)
