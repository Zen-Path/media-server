from datetime import datetime

from ..conftest import API_GET_DOWNLOADS


def test_empty_return(client, auth_headers):
    history = client.get(API_GET_DOWNLOADS, headers=auth_headers).json
    assert len(history) == 0


def test_valid_scenarios(client, auth_headers, seed, sample_download_row):
    """Test that all rows from the database are returned."""
    seeded_rows = seed([sample_download_row])
    target_id = seeded_rows[0].id

    history = client.get(API_GET_DOWNLOADS, headers=auth_headers).json
    assert len(history) == 1

    row = history[0]
    assert row["id"] == target_id
    assert row["title"] == sample_download_row["title"]
    assert row["mediaType"] == sample_download_row["media_type"]
    assert row["orderNumber"] == sample_download_row["order_number"]

    assert "startTime" in row

    actual_start = datetime.fromisoformat(row["startTime"].replace("Z", ""))
    expected_start = sample_download_row["start_time"]
    assert actual_start == expected_start
