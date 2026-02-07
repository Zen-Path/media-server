from unittest.mock import MagicMock, patch

import pytest
from scripts.media_server.app.constants import DownloadStatus, MediaType
from scripts.media_server.app.models.download import Download
from scripts.media_server.app.utils.tools import DownloadReportItem

from ..conftest import API_DOWNLOAD, API_GET_DOWNLOADS


class MockCmdResult:
    def __init__(self, return_code=0, output="Success"):
        self.return_code = return_code
        self.output = output
        self.success = return_code == 0


def test_simple_download(client, auth_headers):
    """Test the download endpoint with mocked external requests."""
    with patch("requests.get") as mock_get:
        mock_title = "Mocked Title"
        mock_url = "https://example.com"

        mock_get.return_value.status_code = 200
        mock_get.return_value.text = f"<html><title>{mock_title}</title></html>"

        payload = {"urls": [mock_url], "mediaType": MediaType.VIDEO}
        response = client.post(API_DOWNLOAD, headers=auth_headers, json=payload)

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"]
        assert data["error"] is None
        assert data["data"] is not None

        first_download = next(iter(data["data"].values()))
        assert first_download["url"] == mock_url
        # TODO: when we'll return Download, then we can check for a title match
        # assert first_download["title"] == mock_title

        # Persistence
        history = client.get(API_GET_DOWNLOADS, headers=auth_headers).json
        assert len(history["data"]) == 1
        assert history["data"][0]["status"] == DownloadStatus.DONE


@pytest.mark.slow
def test_stress(client, auth_headers):
    """Ensure the system doesn't crash or lock up under high request volume."""

    url_count = 50
    for i in range(url_count):
        unique_url = f"https://example.com/image-{i}.png"
        res = client.post(
            API_DOWNLOAD,
            headers=auth_headers,
            json={"urls": [unique_url], "mediaType": MediaType.IMAGE},
        )
        assert res.status_code == 200

    count = Download.query.count()
    assert count == url_count


@pytest.mark.parametrize(
    "test_name, payload, error_msg",
    [
        (
            "urls_missing",
            {},
            "missing data for required field",
        ),
        (
            "urls_none",
            {"urls": None},
            "field may not be null",
        ),
        (
            "urls_wrong_type",
            {"urls": "123"},
            "not a valid list",
        ),
        (
            "media_type_wrong_type",
            {"urls": ["https://example.com"], "mediaType": "Image"},
            "not a valid integer",
        ),
        (
            "media_type_negative_id",
            {"urls": ["https://example.com"], "mediaType": -1},
            "must be one of",
        ),
        (
            "field_snake_case",
            {"urls": ["https://example.com"], "media_type": MediaType.IMAGE},
            "unknown field",
        ),
        (
            "range_start_wrong_type",
            {"urls": ["https://example.com"], "rangeStart": "123"},
            "not a valid integer",
        ),
        (
            "range_end_wrong_type",
            {"urls": ["https://example.com"], "rangeEnd": "123"},
            "not a valid integer",
        ),
    ],
)
def test_invalid_scenarios(test_name, payload, error_msg, client, auth_headers):
    res = client.post(API_DOWNLOAD, headers=auth_headers, json=payload)
    assert res.status_code == 400

    data = res.get_json()
    assert not data["status"]
    assert data["data"] is None
    assert error_msg.lower() in data["error"].lower()


@patch("scripts.media_server.app.routes.api.media.initialize_download")
def test_initial_recording_deduplication(mock_start, client, auth_headers):
    """Verify that the initial recording phase uses list(set(urls))."""
    mock_start.return_value = (True, 1, None)
    urls = ["http://dup.com", "http://dup.com", "http://unique.com"]

    client.post(
        API_DOWNLOAD,
        headers=auth_headers,
        json={"urls": urls, "mediaType": MediaType.IMAGE},
    )

    # Should only be called twice because of the set()
    assert mock_start.call_count == 2


@patch("scripts.media_server.app.routes.api.media.expand_collection_urls")
@patch("scripts.media_server.app.routes.api.media.Gallery.download")
@patch("requests.get")
def test_gallery_expansion_flow(
    mock_get, mock_gallery, mock_expand, client, auth_headers
):
    """Verify Phase 2 correctly expands one URL into multiple child records."""
    parent_url = "http://gallery.com/main"
    child_urls = ["http://gallery.com/1", "http://gallery.com/2"]

    mock_expand.return_value = child_urls
    mock_gallery.return_value = DownloadReportItem(status=True)

    # Mock title scrape response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "<html><title>Test Page</title></html>"
    mock_get.return_value = mock_response

    payload = {"urls": [parent_url], "mediaType": MediaType.GALLERY}
    res = client.post(API_DOWNLOAD, headers=auth_headers, json=payload)

    data = res.get_json()

    assert parent_url in data["data"]
    assert child_urls[0] in data["data"]

    # TODO: When we'll return Download, then we can check for more details


@patch("requests.get")
@patch("scripts.media_server.app.routes.api.media.Gallery.download")
def test_title_scrape_failure_handling(mock_gallery, mock_get, client, auth_headers):
    """
    Verify that a failed title scrape adds a warning but doesn't fail the
    download.
    """
    mock_get.side_effect = Exception("Connection Timeout")
    mock_gallery.return_value = DownloadReportItem(status=True)

    url = "http://slow-site.com/img.jpg"
    res = client.post(
        API_DOWNLOAD,
        headers=auth_headers,
        json={"urls": [url], "mediaType": MediaType.IMAGE},
    )

    data = res.get_json()
    first_download = next(iter(data["data"].values()))

    assert first_download["status"] is True
    assert any("Title scrape failed" in w for w in first_download["warnings"])


@patch("scripts.media_server.app.routes.api.media.expand_collection_urls")
@patch("scripts.media_server.app.routes.api.media.Gallery.download")
def test_gallery_dl_failure_reporting(mock_gallery, mock_expand, client, auth_headers):
    """Verify that a non-zero return code from gallery-dl marks status as False."""
    # TODO: change when adding unit tests
    mock_gallery.return_value = DownloadReportItem(
        status=False, output="403 Forbidden", error="System command failed"
    )
    mock_expand.return_value = []

    url = "http://blocked.com/gallery"
    res = client.post(
        API_DOWNLOAD,
        headers=auth_headers,
        json={"urls": [url], "mediaType": MediaType.GALLERY},
    )

    data = res.get_json()
    first_download = next(iter(data["data"].values()))

    assert first_download["status"] is False
    assert first_download["output"] == "403 Forbidden"
    assert "Command failed".lower() in first_download["error"].lower()


@patch("scripts.media_server.app.routes.api.media.expand_collection_urls")
@patch("scripts.media_server.app.routes.api.media.Gallery.download")
def test_gallery_dl_failure_patterns(mock_gallery, mock_expand, client, auth_headers):
    """Verify that if failure patterns are matched return status is False."""
    # TODO: change when adding unit tests
    mock_gallery.return_value = DownloadReportItem(
        status=False,
        output="[reddit][info] No results for url",
        error="No results found for url.",
    )
    mock_expand.return_value = []

    url = "http://fail.com/gallery"
    res = client.post(
        API_DOWNLOAD,
        headers=auth_headers,
        json={"urls": [url], "mediaType": MediaType.GALLERY},
    )

    data = res.get_json()
    first_download = next(iter(data["data"].values()))

    assert not first_download["status"]
    assert "No results found" in first_download["error"]
    assert "[reddit][info]" in first_download["output"]


@patch("scripts.media_server.app.routes.api.media.expand_collection_urls")
@patch("scripts.media_server.app.routes.api.media.Gallery.download")
def test_return_files(mock_gallery, mock_expand, client, auth_headers):
    """Verify that file paths are return for successful downloads."""
    files = [
        "./dir1/image-1.jpg",
        "./dir1/image-2.jpg",
        "./dir2/image-1.jpg",
    ]
    mock_gallery.return_value = DownloadReportItem(status=True, files=files)
    mock_expand.return_value = []

    url = "https://test.com/gallery"
    res = client.post(
        API_DOWNLOAD,
        headers=auth_headers,
        json={"urls": [url], "mediaType": MediaType.GALLERY},
    )

    data = res.get_json()
    first_download = next(iter(data["data"].values()))

    assert first_download["status"]
    assert len(first_download["files"]) == 3
    assert first_download["files"][0] == "./dir1/image-1.jpg"
