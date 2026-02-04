import logging
import os

from flask import Flask, request
from flask_cors import CORS

from app.constants import APP_VERSION
from app.extensions import db
from app.routes.api import bp as api_bp
from app.routes.main import bp as main_bp
from app.utils.api_response import api_response
from app.utils.logger import logger, setup_logging
from app.utils.seeder import seed_db
from app.utils.sse import MessageAnnouncer


def create_app(config_class):
    app = Flask(__name__)

    # Instantiate the class so @property methods are evaluated
    config_obj = config_class()
    app.config.from_object(config_obj)

    log_level = logging.DEBUG_MODE if app.config.get("DEMO_MODE") else logging.WARNING
    setup_logging(logger, log_level)

    logger.info(f"Starting Media Server v{app.config['APP_VERSION']}")
    logger.debug(f"Download Dir: {app.config['DOWNLOAD_DIR']}")

    CORS(app)  # Enable CORS for all routes
    db.init_app(app)

    app.config["ANNOUNCER"] = MessageAnnouncer()

    # Blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.context_processor
    def inject_global_vars():
        return {
            "project_version": APP_VERSION,
            "github_url": "https://github.com/Zen-Path/flexycon/tree/main/dotfiles/src/scripts/media_server",
            "site_name": "Media Server",
        }

    @app.errorhandler(404)
    def handle_404(e):
        if request.path.startswith("/api/"):
            return api_response(
                error="Not Found",
                data={"message": f"The requested URL {request.path!r} was not found."},
                status_code=404,
            )

        # return render_template("404.html"), 404
        return e

    if app.config.get("DEMO_MODE"):
        with app.app_context():
            logger.info("DEMO MODE ENABLED")

            # Create tables directly (skipping migrations for temp DB)
            db.create_all()

            row_count = int(os.getenv("DEMO_ROW_COUNT", 25))
            seed_db(row_count=row_count)
            logger.info(f"Database seeded with {row_count} rows.")

    return app
