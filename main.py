import logging
import os
import secrets
import tempfile
from pathlib import Path

from dotenv import load_dotenv

from app import app
from app.extensions import db
from app.utils.database import init_db, seed_db
from app.utils.logger import logger, setup_logging
from app.utils.sse import MessageAnnouncer

ENV_PATH = ".env"

load_dotenv(dotenv_path=ENV_PATH)


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
            Path(os.getenv("DATABASE_PATH") or Path("instance") / "media.db").absolute()
        )
    logger.debug(f"Database path: {db_path!r}")

    api_secret_key = os.getenv("API_SECRET_KEY")
    if not api_secret_key:
        api_secret_key = secrets.token_urlsafe(32)
        with open(ENV_PATH, "a") as f:
            f.write(f"\nAPI_SECRET_KEY={api_secret_key}")

        logger.warning(
            f"API_SECRET_KEY not found in environment. Generated val and saved "
            f"to {ENV_PATH!r}"
        )

    app.config.update(
        API_SECRET_KEY=api_secret_key,
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

    raw_port = os.getenv("SERVER_PORT", "5001")

    try:
        server_port = int(raw_port)
    except ValueError:
        server_port = 5001
        logger.warning(
            f"Invalid SERVER_PORT '{raw_port}'. Defaulting to {server_port}."
        )

    if not os.getenv("SERVER_PORT"):
        with open(ENV_PATH, "a") as f:
            f.write(f"\nSERVER_PORT={server_port}")
        logger.warning(f"SERVER_PORT not found. Saved {server_port} to {ENV_PATH!r}")

    app.run(
        port=server_port,
        debug=debug_mode,
        threaded=True,
    )


if __name__ == "__main__":
    main()
