import os
import tempfile
import threading
import time
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from scripts.media_server.main import app
from scripts.media_server.src.constants import MediaType
from scripts.media_server.src.extensions import db
from scripts.media_server.src.models import Download
from scripts.media_server.src.utils.database import seed_db
from scripts.media_server.src.utils.sse import MessageAnnouncer
from werkzeug.serving import make_server

# --- CONFIGURATION ---
TEST_PORT = 5002
BASE_URL = f"http://127.0.0.1:{TEST_PORT}"


@pytest.fixture(scope="session")
def db_instance():
    """
    Sets up the SQLAlchemy database and initializes the app.
    """
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    db_uri = f"sqlite:///{os.path.abspath(db_path)}"

    announcer = MessageAnnouncer()

    app.config.update(
        {
            "SQLALCHEMY_DATABASE_URI": db_uri,
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "SQLALCHEMY_ENGINE_OPTIONS": {"connect_args": {"timeout": 10}},
            "MEDIA_SERVER_KEY": "test-secret-key",
            "TESTING": True,
            "ANNOUNCER": announcer,
        }
    )

    with app.app_context():
        db.init_app(app)
        db.create_all()

    yield db

    # Cleanup after the whole session is done
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture(scope="session", autouse=True)
def run_server(db_instance):
    """
    Launches the Flask server in a background thread.
    """
    server = make_server("127.0.0.1", TEST_PORT, app, threaded=True)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()

    time.sleep(0.5)  # Wait for server to bind

    yield

    server.shutdown()
    server_thread.join()


@pytest.fixture(autouse=True)
def app_context():
    """
    Ensures an application context is active for every single test.
    This fixes the 'Working outside of application context' error.
    """
    with app.app_context():
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
def client(db_instance):
    """
    Flask Test Client for direct API testing.
    """
    with app.test_client() as client:
        yield client


@pytest.fixture
def announcer(db_instance):
    """
    Provides access to the MessageAnnouncer instance stored in the app config.
    """
    return app.config["ANNOUNCER"]


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
API_BULK_DELETE = "/api/bulkDelete"
API_BULK_EDIT = "/api/bulkEdit"
