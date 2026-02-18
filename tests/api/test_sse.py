import json
from unittest.mock import patch

from app.constants import (
    API_DOWNLOADS,
    API_MEDIA_DOWNLOAD,
    DownloadStatus,
    EventType,
    MediaType,
)
from app.utils.tools import DownloadReportItem


def parse_sse(raw_msg: str) -> dict:
    """Strips 'data:' prefix and parses the JSON content."""
    # We use partition to split once at ':', then take everything after
    _, _, json_str = raw_msg.partition(":")
    return json.loads(json_str.strip())


def test_download_announcements(client, announcer, auth_headers):
    """
    Test the full chain of events for a download:
    create -> update (success)
    """
    test_queue = announcer.listen()

    # Define expected data
    target_url = "http://gallery.com"
    target_media_type = MediaType.GALLERY
    mock_title = "SSE Gallery"

    with patch("app.services.execution_service.scrape_title") as mock_scrape:
        mock_scrape.return_value = mock_title

        with patch("app.services.execution_service.Gallery.download") as mock_dl:
            mock_dl.return_value = DownloadReportItem(status=True)

            payload = {"items": [{"url": target_url, "mediaType": target_media_type}]}
            res = client.post(API_MEDIA_DOWNLOAD, headers=auth_headers, json=payload)
            assert res.status_code == 200

            mock_scrape.assert_called_once_with(target_url)

    # Expect CREATE
    msg_create = parse_sse(test_queue.get(timeout=2))
    assert msg_create["type"] == EventType.CREATE

    create_data = msg_create["data"][0]
    print("Create data: ", create_data)

    assert create_data["id"] is not None
    assert create_data["url"] == target_url
    assert create_data["mediaType"] == target_media_type
    assert isinstance(create_data["startTime"], int)

    # Expect UPDATE
    msg_update = parse_sse(test_queue.get(timeout=2))
    assert msg_update["type"] == EventType.UPDATE

    update_data = msg_update["data"][0]
    print("Update data: ", update_data)

    assert update_data["id"] == create_data["id"]
    assert update_data["title"] == mock_title
    assert isinstance(update_data["endTime"], int)
    assert update_data["status"] == DownloadStatus.DONE
    assert "statusMessage" in update_data


def test_system_resilience_to_announcer_failure(client, auth_headers, seed):
    """
    If the event announcer crashes, the API should still work (Graceful Degradation).
    """
    seed([{"url": "test.com", "id": 100}])

    with patch("app.utils.sse.MessageAnnouncer.announce") as mock_announce:
        mock_announce.side_effect = Exception("Socket Connection Lost")

        # Try to delete. Even if the dashboard notification fails, the DB delete
        # should happen.
        res = client.delete(API_DOWNLOADS, headers=auth_headers, json={"ids": [100]})

        assert res.status_code == 200
        assert res.get_json()["status"] is True
