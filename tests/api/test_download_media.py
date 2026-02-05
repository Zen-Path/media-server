from unittest.mock import MagicMock, patch

import pytest
from scripts.media_server.src.constants import DownloadStatus, MediaType
from scripts.media_server.src.models.download import Download

from ..conftest import API_DOWNLOAD, API_GET_DOWNLOADS


class MockCmdResult:
    def __init__(self, return_code=0, output="Success"):
        self.return_code = return_code
        self.output = output
        self.success = return_code == 0


def test_simple_download(client, auth_headers):
    """Test the download endpoint with mocked external requests."""
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = "<html><title>Mocked Title</title></html>"

        payload = {"urls": ["http://mock-site.com"], "mediaType": MediaType.VIDEO}
        response = client.post(API_DOWNLOAD, headers=auth_headers, json=payload)

        assert response.status_code == 200
        assert len(response.json) == 1

        history = client.get(API_GET_DOWNLOADS, headers=auth_headers).json
        print(history)
        assert len(history) == 1
        assert history[0]["status"] == DownloadStatus.DONE


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


def test_download_media_invalid_input(client, auth_headers):
    """Verify that bad payloads return 400."""
    # Test missing URLs
    res = client.post(
        API_DOWNLOAD, headers=auth_headers, json={"mediaType": MediaType.IMAGE}
    )
    assert res.status_code == 400

    # Test bad range
    res = client.post(
        API_DOWNLOAD,
        headers=auth_headers,
        json={
            "urls": ["http://test.com"],
            "mediaType": MediaType.GALLERY,
            "rangeStart": "not-an-int",
        },
    )
    assert res.status_code == 400


@patch("scripts.media_server.routes.api.media.start_download_record")
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


@patch("scripts.media_server.routes.api.media.expand_collection_urls")
@patch("scripts.media_server.routes.api.media.Gallery.download")
@patch("requests.get")
def test_gallery_expansion_flow(
    mock_get, mock_gallery, mock_expand, client, auth_headers
):
    """Verify Phase 2 correctly expands one URL into multiple child records."""
    parent_url = "http://gallery.com/main"
    child_urls = ["http://gallery.com/1", "http://gallery.com/2"]

    mock_expand.return_value = child_urls
    mock_gallery.return_value = MockCmdResult(0)

    # Mock title scrape response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "<html><title>Test Page</title></html>"
    mock_get.return_value = mock_response

    payload = {"urls": [parent_url], "mediaType": MediaType.GALLERY}
    res = client.post(API_DOWNLOAD, headers=auth_headers, json=payload)

    data = res.get_json()
    print(data)

    # Check parent entry
    assert parent_url in data
    assert "Expanded into 2 items" in data[parent_url]["log"]

    # Check child entries exist in the report
    assert child_urls[0] in data
    # TODO: when we'll return the created Download, we can check the parent id
    # assert data[child_urls[0]]["log"] == "Child of #1"


@patch("requests.get")
@patch("scripts.media_server.routes.api.media.Gallery.download")
def test_title_scrape_failure_handling(mock_gallery, mock_get, client, auth_headers):
    """
    Verify that a failed title scrape adds a warning but doesn't fail the
    download.
    """
    mock_get.side_effect = Exception("Connection Timeout")
    mock_gallery.return_value = MockCmdResult(0)

    url = "http://slow-site.com/img.jpg"
    res = client.post(
        API_DOWNLOAD,
        headers=auth_headers,
        json={"urls": [url], "mediaType": MediaType.IMAGE},
    )

    data = res.get_json()
    assert data[url]["status"] is True
    assert any("Title scrape failed" in w for w in data[url]["warnings"])


@patch("scripts.media_server.routes.api.media.expand_collection_urls")
@patch("scripts.media_server.routes.api.media.Gallery.download")
def test_gallery_dl_failure_reporting(mock_gallery, mock_expand, client, auth_headers):
    """Verify that a non-zero return code from gallery-dl marks status as False."""
    mock_gallery.return_value = MockCmdResult(return_code=1, output="403 Forbidden")
    mock_expand.return_value = []

    url = "http://blocked.com/gallery"
    res = client.post(
        API_DOWNLOAD,
        headers=auth_headers,
        json={"urls": [url], "mediaType": MediaType.GALLERY},
    )

    data = res.get_json()
    assert data[url]["status"] is False
    assert data[url]["output"] == "403 Forbidden"
    assert "Command failed" in data[url]["error"]


@patch("scripts.media_server.routes.api.media.expand_collection_urls")
@patch("scripts.media_server.routes.api.media.Gallery.download")
def test_gallery_dl_failure_patterns(mock_gallery, mock_expand, client, auth_headers):
    """Verify that if failure patterns are matched return status is False."""
    mock_gallery.return_value = MockCmdResult(
        return_code=0, output="[reddit][info] No results for url"
    )
    mock_expand.return_value = []

    url = "http://fail.com/gallery"
    res = client.post(
        API_DOWNLOAD,
        headers=auth_headers,
        json={"urls": [url], "mediaType": MediaType.GALLERY},
    )

    data = res.get_json()
    assert not data[url]["status"]
    assert "No results found" in data[url]["error"]
    assert "[reddit][info]" in data[url]["output"]


@patch("scripts.media_server.routes.api.media.expand_collection_urls")
@patch("scripts.media_server.routes.api.media.Gallery.download")
def test_return_files(mock_gallery, mock_expand, client, auth_headers):
    """Verify that file paths are return for successful downloads."""
    files = [
        "./dir1/image-1.jpg",
        "./dir1/image-2.jpg",
        "./dir2/image-1.jpg",
    ]
    mock_gallery.return_value = MockCmdResult(return_code=0, output="\n".join(files))
    mock_expand.return_value = []

    url = "https://test.com/gallery"
    res = client.post(
        API_DOWNLOAD,
        headers=auth_headers,
        json={"urls": [url], "mediaType": MediaType.GALLERY},
    )

    data = res.get_json()
    print(data)
    assert data[url]["status"]
    assert len(data[url]["files"]) == 3
    assert data[url]["files"][0] == "./dir1/image-1.jpg"
    assert "./dir1/image-1.jpg" in data[url]["output"]
