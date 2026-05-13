from app import app


if __name__ == "__main__":
    debug_mode = bool(app.config.get("RUN_DEBUG", False))
    app.run(debug=debug_mode, use_reloader=debug_mode)
