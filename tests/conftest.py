import os
import tempfile
import threading
import time
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from werkzeug.serving import make_server

from app import create_app
from app.constants import MediaType
from app.extensions import db
from app.models.download import Download
from app.utils.seeder import seed_db
from config import TestConfig

# --- CONFIGURATION ---
TEST_PORT = 5002
BASE_URL = f"http://127.0.0.1:{TEST_PORT}"


@pytest.fixture(scope="session")
def test_app():
    """
    Creates the Flask application object for the test session.
    Handles the temporary database file creation and configuration.
    """
    # 1. Setup Temp DB File
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    db_uri = f"sqlite:///{os.path.abspath(db_path)}"

    # 2. Create App & Override Config
    app = create_app(TestConfig)
    app.config.update(
        {
            "SQLALCHEMY_DATABASE_URI": db_uri,
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "MEDIA_SERVER_KEY": "test-secret-key",
            "TESTING": True,
            # ANNOUNCER is initialized automatically in create_app
        }
    )

    # 3. Establish Context & Yield
    # We keep the app context active for the session so db_instance can work
    with app.app_context():
        yield app

    # 4. Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture(scope="session")
def db_instance(test_app):
    """
    Sets up the SQLAlchemy database schema.
    Depends on test_app to ensure the app context is active.
    """
    # db.init_app(app) was already called in create_app()
    db.create_all()

    yield db

    db.session.remove()
    db.drop_all()


@pytest.fixture(scope="session", autouse=True)
def run_server(test_app, db_instance):
    """
    Launches the Flask server in a background thread.
    """
    server = make_server("127.0.0.1", TEST_PORT, test_app, threaded=True)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()

    time.sleep(0.5)  # Wait for server to bind

    yield

    server.shutdown()
    server_thread.join()


@pytest.fixture(autouse=True)
def app_context(test_app):
    """
    Ensures an application context is active for every single test.
    This fixes the 'Working outside of application context' error.
    """
    with test_app.app_context():
        yield


@pytest.fixture(autouse=True)
def clean_db(db_instance):
    """
    Since we use a background server, we must commit data for the server to see it.
    Therefore, we manually delete all rows after each test to ensure isolation.
    """
    yield  # Run the test

    db.session.query(Download).delete()
    db.session.commit()


@pytest.fixture
def seed(db_instance):
    """Wrapper fixture for the seed_db utility."""

    def _seed(data=None):
        return seed_db(data)

    return _seed


@pytest.fixture
def client(test_app, db_instance):
    """
    Flask Test Client for direct API testing.
    """
    with test_app.test_client() as client:
        yield client


@pytest.fixture
def announcer(test_app, db_instance):
    """
    Provides access to the MessageAnnouncer instance stored in the app config.
    """
    return test_app.config["ANNOUNCER"]


@pytest.fixture
def auth_headers():
    return {"X-API-Key": "test-secret-key"}


@pytest.fixture
def create_mock_cursor():
    """Returns a factory function to create a cursor with a specific rowcount."""

    def _create(row_count=1):
        cursor = MagicMock()
        cursor.rowcount = row_count
        return cursor

    return _create


@pytest.fixture
def sample_download_row():
    return {
        "url": "https://www.test.com/image-1.jpg",
        "title": "Test Page",
        "media_type": MediaType.IMAGE,
        "start_time": datetime.fromisoformat("2025-01-01T10:10:15"),
        "end_time": datetime.fromisoformat("2025-01-01T10:11:20"),
        "order_number": 0,
    }


API_GET_DOWNLOADS = "/api/downloads"
API_HEALTH = "/api/health"
API_STREAM = "/api/events"
API_DOWNLOAD = "/api/media/download"
API_BULK_DELETE = "/api/downloads"
API_BULK_EDIT = "/api/downloads"
