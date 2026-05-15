import logging
from typing import Any

from flask import Flask, current_app, render_template, request
from werkzeug.exceptions import (
    BadRequest,
    HTTPException,
    RequestEntityTooLarge,
    UnprocessableEntity,
    UnsupportedMediaType,
)

logger = logging.getLogger(__name__)


def is_html_request() -> bool:
    """Detect whether the caller prefers HTML over JSON responses.
    Used to keep browser form UX and API-style callers both supported."""
    accept = request.accept_mimetypes
    return accept["text/html"] >= accept["application/json"]


def error_response(message: str, status_code: int) -> tuple[Any, int]:
    """Build a unified error payload for browser and non-browser clients.
    Renders template errors for HTML requests and JSON otherwise."""
    if is_html_request():
        return render_template("index.html", error_message=message), status_code
    return {"error": message}, status_code


def register_error_handlers(app: Flask) -> None:
    """Register all HTTP and unexpected error handlers on the app.
    Preserves consistent response schema and user-facing messaging."""
    @app.errorhandler(RequestEntityTooLarge)
    def handle_request_too_large(exc: RequestEntityTooLarge):
        _ = exc
        max_mb = current_app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024)
        return error_response(
            f"Uploaded file is too large. Maximum allowed size is {max_mb} MB.",
            413,
        )

    @app.errorhandler(BadRequest)
    def handle_bad_request(exc: BadRequest):
        return error_response(exc.description or "Invalid request.", 400)

    @app.errorhandler(UnsupportedMediaType)
    def handle_unsupported_media_type(exc: UnsupportedMediaType):
        return error_response(exc.description or "Unsupported media type.", 415)

    @app.errorhandler(UnprocessableEntity)
    def handle_unprocessable_entity(exc: UnprocessableEntity):
        return error_response(exc.description or "Unable to process uploaded CV.", 422)

    @app.errorhandler(HTTPException)
    def handle_http_exception(exc: HTTPException):
        return error_response(exc.description or "Request failed.", exc.code or 500)

    @app.errorhandler(Exception)
    def handle_unexpected_error(exc: Exception):
        logger.exception("Unexpected server error", exc_info=exc)
        return error_response("Internal server error.", 500)
