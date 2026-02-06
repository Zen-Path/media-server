import json
from unittest.mock import MagicMock, patch

from scripts.media_server.app.constants import EventType, MediaType

from ..conftest import API_BULK_DELETE, API_DOWNLOAD


def parse_sse(raw_msg: str) -> dict:
    """Strips 'data:' prefix and parses the JSON content."""
    # We use partition to split once at ':', then take everything after
    _, _, json_str = raw_msg.partition(":")
    return json.loads(json_str.strip())


def test_download_announcements(client, announcer, auth_headers):
    """
    Test the full chain of events for a download:
    create -> progress -> update
    """
    test_queue = announcer.listen()

    # Mock the internal download logic
    with (
        patch("requests.get") as mock_get,
        patch("scripts.media_server.app.utils.downloaders.Gallery.download") as mock_dl,
    ):
        # Mock title scrape
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "<html><title>SSE Gallery</title></html>"
        mock_get.return_value = mock_resp

        # Mock successful download
        mock_result = MagicMock()
        mock_result.return_code = 0
        mock_result.output = "Successful mock download"
        mock_dl.return_value = mock_result

        payload = {"urls": ["http://gallery.com"], "mediaType": MediaType.GALLERY}
        res = client.post(API_DOWNLOAD, headers=auth_headers, json=payload)
        assert res.status_code == 200

    # Expect CREATE
    msg_create = parse_sse(test_queue.get(timeout=2))
    assert msg_create["type"] == EventType.CREATE
    download_id = msg_create["data"]["id"]
    assert "mediaType" in msg_create["data"]
    assert "startTime" in msg_create["data"]

    # Expect PROGRESS
    msg_progress = parse_sse(test_queue.get(timeout=2))
    assert msg_progress["type"] == EventType.PROGRESS
    assert msg_progress["data"]["id"] == download_id
    assert "current" in msg_progress["data"]
    assert "total" in msg_progress["data"]

    # Expect UPDATE
    msg_update = parse_sse(test_queue.get(timeout=2))
    assert msg_update["type"] == EventType.UPDATE
    assert msg_update["data"]["id"] == download_id
    assert msg_update["data"]["title"] == "SSE Gallery"
    assert "endTime" in msg_update["data"]


def test_system_resilience_to_announcer_failure(client, auth_headers, seed):
    """
    If the event announcer crashes, the API should still work (Graceful Degradation).
    """
    seed([{"url": "test.com", "id": 100}])

    with patch(
        "scripts.media_server.app.utils.sse.MessageAnnouncer.announce"
    ) as mock_announce:
        mock_announce.side_effect = Exception("Socket Connection Lost")

        # Try to delete. Even if the dashboard notification fails, the DB delete
        # should happen.
        res = client.post(API_BULK_DELETE, headers=auth_headers, json={"ids": [100]})

        assert res.status_code == 200
        assert res.get_json()["status"] is True
