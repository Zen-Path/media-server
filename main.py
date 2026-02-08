#!{{@@ env['FLEXYCON_HOME'] @@}}/{{@@ d_venv_bin @@}}/python

# {{@@ header() @@}}

import logging
import os
import tempfile
from pathlib import Path

from common.logger import logger, setup_logging
from common.variables import flex_scripts
from dotenv import load_dotenv
from scripts.media_server.app import app
from scripts.media_server.app.extensions import db
from scripts.media_server.app.utils.database import init_db, seed_db
from scripts.media_server.app.utils.sse import MessageAnnouncer

load_dotenv(flex_scripts / "media_server" / ".env")


def main():
    debug_mode = bool(int(os.getenv("DEBUG", "0")))
    demo_mode = bool(int(os.getenv("DEMO", 0)))

    setup_logging(logger, logging.DEBUG if debug_mode else logging.WARNING)

    logger.info(f"Version: {app.config.get('APP_VERSION')}")

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
        MEDIA_SERVER_KEY="{{@@ _vars['media_server_key'] @@}}",
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{db_path}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        ANNOUNCER=MessageAnnouncer(),
        DOWNLOAD_DIR=download_dir,
    )

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
