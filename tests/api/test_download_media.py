from unittest.mock import MagicMock, patch

import pytest

from app.constants import DownloadStatus, MediaType
from app.models.download import Download
from app.utils.tools import DownloadReportItem

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

        payload = {"items": [{"url": mock_url, "mediaType": MediaType.VIDEO}]}
        response = client.post(API_DOWNLOAD, headers=auth_headers, json=payload)
        assert response.status_code == 200

        resp_data = response.get_json()
        assert resp_data["status"]
        assert resp_data["error"] is None

        assert isinstance(resp_data["data"], list)
        assert len(resp_data["data"]) == 1
        assert isinstance(resp_data["data"][0], dict)

        first_download = resp_data["data"][0]
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
            json={"items": [{"url": unique_url, "mediaType": MediaType.IMAGE}]},
        )
        assert res.status_code == 200

    count = Download.query.count()
    assert count == url_count


@pytest.mark.parametrize(
    "payload, error_msg",
    [
        ({}, "missing json payload"),
        ({"items": []}, "shorter than minimum length"),
        ({"items": [{"url": None}]}, "field may not be null"),
        ({"items": [{"url": "123"}]}, "not a valid url"),
        (
            {"items": [{"url": "https://example.com", "mediaType": "Image"}]},
            "not a valid integer",
        ),
        (
            {"items": [{"url": "https://example.com", "mediaType": -1}]},
            "must be one of",
        ),
        (
            {"items": [{"url": "https://example.com", "media_type": MediaType.IMAGE}]},
            "unknown field",
        ),
        (
            {"items": [{"url": "https://example.com"}], "rangeStart": "123"},
            "not a valid integer",
        ),
        (
            {"items": [{"url": "https://example.com"}], "rangeEnd": "123"},
            "not a valid integer",
        ),
    ],
    ids=[
        "items_missing",
        "items_empty",
        "url_none",
        "url_wrong_type",
        "media_type_wrong_type",
        "media_type_negative_id",
        "field_snake_case",
        "range_start_wrong_type",
        "range_end_wrong_type",
    ],
)
def test_invalid_scenarios(payload, error_msg, client, auth_headers):
    res = client.post(API_DOWNLOAD, headers=auth_headers, json=payload)
    assert res.status_code == 400

    data = res.get_json()
    assert not data["status"]
    assert data["data"] is None
    assert error_msg.lower() in data["error"].lower()


@patch("app.routes.api.media.initialize_download")
def test_initial_recording_deduplication(mock_start, client, auth_headers):
    """Verify that the initial recording phase uses list(set(urls))."""
    mock_start.return_value = (True, 1, None)
    urls = ["http://dup.com", "http://dup.com", "http://unique.com"]

    items_data = [{"url": url, "mediaType": MediaType.IMAGE} for url in urls]

    client.post(
        API_DOWNLOAD,
        headers=auth_headers,
        json={"items": items_data},
    )

    # Should only be called twice because of the set()
    assert mock_start.call_count == 2


@patch("app.routes.api.media.expand_collection_urls")
@patch("app.routes.api.media.Gallery.download")
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

    payload = {"items": [{"url": parent_url, "mediaType": MediaType.GALLERY}]}
    resp_data = client.post(API_DOWNLOAD, headers=auth_headers, json=payload)

    data = resp_data.get_json()
    assert any(parent_url == download_data["url"] for download_data in data["data"])
    assert any(child_urls[0] == download_data["url"] for download_data in data["data"])

    # TODO: When we'll return Download, then we can check for more details


@patch("requests.get")
@patch("app.routes.api.media.Gallery.download")
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
        json={"items": [{"url": url, "mediaType": MediaType.IMAGE}]},
    )

    data = res.get_json()
    first_download = data["data"][0]

    assert first_download["status"] is True


@patch("app.routes.api.media.Gallery.download")
def test_gallery_dl_failure_reporting(mock_gallery, client, auth_headers):
    """Verify that a non-zero return code from gallery-dl marks status as False."""
    # TODO: change when adding unit tests
    mock_gallery.return_value = DownloadReportItem(
        status=False, output="403 Forbidden", error="System command failed"
    )

    url = "https://example.com"
    resp_data = client.post(
        API_DOWNLOAD,
        headers=auth_headers,
        json={"items": [{"url": url, "mediaType": MediaType.GALLERY}]},
    )

    data = resp_data.get_json()
    first_download = data["data"][0]

    assert first_download["status"] is False
    assert first_download["output"] == "403 Forbidden"
    assert "Command failed".lower() in first_download["error"].lower()


@patch("app.routes.api.media.Gallery.download")
def test_gallery_dl_failure_patterns(mock_gallery, client, auth_headers):
    """Verify that if failure patterns are matched return status is False."""
    # TODO: change when adding unit tests
    mock_gallery.return_value = DownloadReportItem(
        status=False,
        output="[reddit][info] No results for url",
        error="No results found for url.",
    )

    url = "https://example.com"
    resp_data = client.post(
        API_DOWNLOAD,
        headers=auth_headers,
        json={"items": [{"url": url, "mediaType": MediaType.GALLERY}]},
    )

    data = resp_data.get_json()
    first_download = data["data"][0]

    assert not first_download["status"]
    assert "No results found" in first_download["error"]
    assert "[reddit][info]" in first_download["output"]


@patch("app.routes.api.media.Gallery.download")
def test_return_files(mock_gallery, client, auth_headers):
    """Verify that file paths are return for successful downloads."""
    files = [
        "./dir1/image-1.jpg",
        "./dir1/image-2.jpg",
        "./dir2/image-1.jpg",
    ]
    mock_gallery.return_value = DownloadReportItem(status=True, files=files)

    url = "https://example.com"
    res = client.post(
        API_DOWNLOAD,
        headers=auth_headers,
        json={"items": [{"url": url, "mediaType": MediaType.GALLERY}]},
    )

    data = res.get_json()
    first_download = data["data"][0]

    assert first_download["status"]
    assert len(first_download["files"]) == 3
    assert first_download["files"][0] == "./dir1/image-1.jpg"
