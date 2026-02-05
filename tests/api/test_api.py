import concurrent.futures
from unittest.mock import patch

import requests
from scripts.media_server.src.extensions import db
from scripts.media_server.tests.conftest import (
    API_BULK_DELETE,
    API_GET_DOWNLOADS,
    API_HEALTH,
    BASE_URL,
)
from sqlalchemy.exc import SQLAlchemyError


def test_health_check(client):
    response = client.get(API_HEALTH)
    assert response.status_code == 200

    data = response.json
    assert data["status"] == "ok"


def test_auth(client, auth_headers, seed):
    """Verify that API endpoints require a key."""
    no_key_response = client.get(API_GET_DOWNLOADS)
    assert no_key_response.status_code == 401

    invalid_key_response = client.get(
        API_GET_DOWNLOADS, headers={"X-API-Key": "abc123"}
    )
    assert invalid_key_response.status_code == 401

    valid_key_response = client.get(API_GET_DOWNLOADS, headers=auth_headers)
    assert valid_key_response.status_code == 200


def test_wrong_method(client, auth_headers):
    """Sending a POST request to a GET endpoint"""
    res = client.post(API_GET_DOWNLOADS, headers=auth_headers)

    assert res.status_code == 405


def test_no_content_type_header(client, auth_headers):
    """Sending data without the 'application/json' header"""
    res = client.post(API_BULK_DELETE, headers=auth_headers, data="{}")

    assert res.status_code == 415


def test_api_returns_json_404(client, auth_headers):
    """Ensure that non-existent routes under /api return JSON, not HTML."""
    res = client.get("/api/v1/this-does-not-exist", headers=auth_headers)

    assert res.status_code == 404
    assert res.is_json

    data = res.get_json()
    assert data["status"] is False
    assert "error" in data
    assert "not found" in data["message"].lower()


def test_database_exception(client, auth_headers, seed):
    """
    Test behavior when SQLAlchemy throws an actual operational error during commit.
    """
    seed([{"url": "https://test.com"}])

    # Patch db.session.commit to raise an exception
    with patch.object(
        db.session, "commit", side_effect=SQLAlchemyError("Database Locked")
    ):
        res = client.post(API_BULK_DELETE, headers=auth_headers, json={"ids": [1]})

        data = res.get_json()
        print(data)

        assert not data["status"]
        assert "Database Locked" in data["error"]

    # Ensure the session is rolled back so following tests aren't affected
    db.session.rollback()


def test_massive_payload_handling(client, auth_headers):
    """Verify system doesn't crash with a massive list of IDs."""
    massive_ids = list(range(10000))
    res = client.post(API_BULK_DELETE, headers=auth_headers, json={"ids": massive_ids})
    # The system should either process it or return a controlled error, not 500
    assert res.status_code in [200, 413]  # 413 is Request Entity Too Large


def test_concurrent_operations(client, auth_headers, seed):
    """Stress test the DB by hitting it from multiple threads simultaneously."""
    seed([{"url": f"https://test{i}.com"} for i in range(50)])

    def make_request(i):
        # Every thread tries to delete the same IDs to force a collision/race
        return requests.post(
            f"{BASE_URL}/{API_BULK_DELETE}",
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
