import logging
from pathlib import Path
from typing import Any, Mapping

from flask import Flask

from web.config import runtime_config
from web.errors import register_error_handlers
from web.routes import web_bp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()],
)


def create_app(test_config: Mapping[str, Any] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(runtime_config(Path(__file__).resolve().parent))

    if test_config is not None:
        app.config.from_mapping(test_config)

    upload_folder = Path(app.config["UPLOAD_FOLDER"])
    upload_folder.mkdir(parents=True, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = upload_folder

    app.register_blueprint(web_bp)
    register_error_handlers(app)

    return app


app = create_app()


if __name__ == "__main__":
    debug_mode = bool(app.config.get("RUN_DEBUG", False))
    app.run(debug=debug_mode, use_reloader=debug_mode)
