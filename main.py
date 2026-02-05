#!{{@@ env['FLEXYCON_HOME'] @@}}/{{@@ d_venv_bin @@}}/python

# {{@@ header() @@}}

import logging
import os
import tempfile
from pathlib import Path

from common.logger import logger, setup_logging
from common.variables import flex_scripts
from dotenv import load_dotenv
from flask import Flask, abort, current_app, jsonify, request
from flask_cors import CORS
from scripts.media_server.routes.api import bp as api_bp
from scripts.media_server.routes.main import bp as main_bp
from scripts.media_server.src.logging_middleware import register_logging
from scripts.media_server.src.models import db
from scripts.media_server.src.utils.database import init_db, seed_db
from scripts.media_server.src.utils.sse import MessageAnnouncer

__version__ = "3.2.1"

load_dotenv(flex_scripts / "media_server" / ".env")

app = Flask(
    __name__,
    template_folder=Path(flex_scripts / "media_server" / "templates"),
    static_folder=Path(flex_scripts / "media_server" / "static"),
)

app.register_blueprint(main_bp)
app.register_blueprint(api_bp, url_prefix="/api")


@app.before_request
def check_auth():
    if request.path.startswith("/api/") and request.path != "/api/health":
        # Check header OR query string (for SSE)
        provided_key = request.headers.get("X-API-Key") or request.args.get("apiKey")

        expected_key = current_app.config.get("MEDIA_SERVER_KEY")
        if not provided_key or provided_key != expected_key:
            abort(401)


@app.errorhandler(404)
def handle_404(e):
    # Only return JSON if the request was directed at the API
    if request.path.startswith("/api/"):
        return (
            jsonify(
                {
                    "status": False,
                    "error": "Not Found",
                    "message": f"The requested URL {request.path!r} was not found.",
                }
            ),
            404,
        )

    return e


@app.context_processor
def inject_global_vars():
    return {
        "project_version": __version__,
        "github_url": "https://github.com/Zen-Path/flexycon/tree/main/dotfiles/src/scripts/media_server",
        "site_name": "Media Server",
    }


def main():
    debug_mode = bool(int(os.getenv("DEBUG", "0")))
    demo_mode = bool(int(os.getenv("DEMO", 0)))

    setup_logging(logger, logging.DEBUG if debug_mode else logging.WARNING)

    logger.info(f"Version: {__version__}")

    # .env value > xdg value > fallback location
    download_dir = Path(
        os.getenv("DOWNLOAD_DIR") or os.getenv("XDG_DOWNLOAD_DIR") or "downloads"
    )
    logger.debug(f"Download dir: {download_dir}")

    # Needs to be an abs path
    if demo_mode:
        db_fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(db_fd)
    else:
        db_path = str(
            Path(
                os.getenv("DB_PATH") or flex_scripts / "media_server" / "media.db"
            ).absolute()
        )
    logger.debug(f"Database path: {db_path!r}")

    app.config.update(
        APP_VERSION=__version__,
        MEDIA_SERVER_KEY="{{@@ _vars['media_server_key'] @@}}",
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{db_path}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        ANNOUNCER=MessageAnnouncer(),
        DOWNLOAD_DIR=download_dir,
    )

    CORS(app)  # Enable CORS for all routes
    register_logging(app)

    db.init_app(app)

    with app.app_context():
        init_db(app)

        if demo_mode:
            logger.info("Demo mode enabled!")

            row_count = int(os.getenv("DEMO_ROW_COUNT", 25))
            logger.info(f"Seeding database with {row_count} rows...")
            seed_db(row_count=row_count)

    app.run(
        port=int("{{@@ _vars['media_server_port'] @@}}"),
        debug=debug_mode,
        threaded=True,
    )


if __name__ == "__main__":
    main()
