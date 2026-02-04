import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


class Config:
    APP_VERSION = "3.2.1"
    MEDIA_SERVER_KEY = os.environ.get("MEDIA_SERVER_KEY") or "default-key"

    DOWNLOAD_DIR = Path(
        os.getenv("DOWNLOAD_DIR")
        or os.getenv("XDG_DOWNLOAD_DIR")
        or os.path.join(basedir, "downloads")
    )

    DEBUG_MODE = bool(int(os.getenv("DEBUG", "0")))
    DEMO_MODE = bool(int(os.getenv("DEMO", "0")))

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @property
    def SQLALCHEMY_DATABASE_URI(self):
        """
        Dynamic property to handle Demo mode's ephemeral database.
        """
        if self.DEMO_MODE:
            # Create a temporary file that persists only for this run
            db_fd, db_path = tempfile.mkstemp(suffix=".db")
            os.close(db_fd)
            return f"sqlite:///{db_path}"

        # Normal mode
        db_path = os.environ.get("DB_PATH") or os.path.join(basedir, "media.db")
        return f"sqlite:///{os.path.abspath(db_path)}"


class TestConfig(Config):
    TESTING = True
