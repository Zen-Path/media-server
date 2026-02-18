import concurrent.futures
from datetime import datetime
from unittest.mock import patch

import pytest
import requests
from sqlalchemy.exc import SQLAlchemyError

from app.constants import API_DOWNLOADS, API_HEALTH
from app.extensions import db
from tests.conftest import BASE_URL


def test_auth_valid(client, auth_headers):
    """
    Verify that API endpoints accept valid credentials via header and query string.
    """
    resp = client.get(API_DOWNLOADS, headers=auth_headers)
    assert resp.status_code == 200

    valid_key = auth_headers["X-API-Key"]
    resp = client.get(API_DOWNLOADS, query_string={"apiKey": valid_key})
    assert resp.status_code == 200


INVALID_KEY = "abc123_invalid"


@pytest.mark.parametrize(
    "request_kwargs",
    [
        {},
        {"headers": {"X-API-Key": INVALID_KEY}},
        {"query_string": {"apiKey": INVALID_KEY}},
    ],
    ids=["missing_both", "bad_header", "bad_query"],
)
def test_auth_invalid(client, request_kwargs):
    """
    Verify that API endpoints reject missing or invalid credentials via headers or
    query args.
    """
    resp = client.get(API_DOWNLOADS, **request_kwargs)
    assert resp.status_code == 401


def test_health_check(client):
    response = client.get(API_HEALTH)
    assert response.status_code == 200

    payload = response.json

    assert payload["status"] == "ok"
    assert payload["error"] is None

    assert "data" in payload
    assert isinstance(payload["data"], dict)

    expected_version = client.application.config.get("APP_VERSION")
    assert payload["data"]["version"] == expected_version

    try:
        datetime.fromisoformat(payload["data"]["timestamp"])
    except ValueError:
        pytest.fail("Timestamp format is invalid")


def test_wrong_method(client, auth_headers):
    """Sending a POST request to a GET endpoint"""
    res = client.post(API_DOWNLOADS, headers=auth_headers)

    assert res.status_code == 405


def test_no_content_type_header(client, auth_headers):
    """Sending data without the 'application/json' header"""
    res = client.delete(API_DOWNLOADS, headers=auth_headers, data="{}")

    assert res.status_code == 415


def test_api_returns_json_404(client, auth_headers):
    """Ensure that non-existent routes under /api return JSON, not HTML."""
    res = client.get("/api/v1/this-does-not-exist", headers=auth_headers)

    assert res.status_code == 404
    assert res.is_json

    data = res.get_json()
    assert data["status"] is False
    assert data["error"] == "Not Found"

    assert "message" in data["data"]
    assert "The requested URL".lower() in data["data"]["message"].lower()


def test_database_exception(client, auth_headers, seed):
    """
    Test behavior when SQLAlchemy throws an actual operational error during commit.
    """
    seed([{"url": "https://test.com"}])

    # Patch db.session.commit to raise an exception
    with patch.object(
        db.session, "commit", side_effect=SQLAlchemyError("Database Locked")
    ):
        res = client.delete(API_DOWNLOADS, headers=auth_headers, json={"ids": [1]})

        data = res.get_json()
        print(data)

        assert not data["status"]
        assert "Database Locked" in data["error"]

    # Ensure the session is rolled back so following tests aren't affected
    db.session.rollback()


def test_massive_payload_handling(client, auth_headers):
    """Verify system doesn't crash with a massive list of IDs."""
    massive_ids = list(range(10000))
    res = client.delete(API_DOWNLOADS, headers=auth_headers, json={"ids": massive_ids})
    # The system should either process it or return a controlled error, not 500
    assert res.status_code in [200, 413]  # 413 is Request Entity Too Large


def test_concurrent_operations(client, auth_headers, seed):
    """Stress test the DB by hitting it from multiple threads simultaneously."""
    seed([{"url": f"https://test{i}.com"} for i in range(50)])

    def make_request(i):
        # Every thread tries to delete the same IDs to force a collision/race
        return requests.delete(
            f"{BASE_URL}/{API_DOWNLOADS}",
            headers=auth_headers,
            json={"ids": list(range(1, 51))},
            timeout=5,
        )

    # Simulate 10 simultaneous users
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request, i) for i in range(10)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # None should cause a 500 server crash
    for res in results:
        assert res.status_code == 200
