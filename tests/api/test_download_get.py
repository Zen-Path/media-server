from ..conftest import API_GET_DOWNLOADS


def test_empty_return(client, auth_headers):
    history = client.get(API_GET_DOWNLOADS, headers=auth_headers).json
    assert len(history["data"]) == 0


def test_valid_scenarios(client, auth_headers, seed, sample_download_row):
    """Test that all rows from the database are returned."""
    seeded_rows = seed([sample_download_row])
    target_id = seeded_rows[0].id

    history = client.get(API_GET_DOWNLOADS, headers=auth_headers).json
    assert len(history["data"]) == 1

    row = history["data"][0]
    assert row["id"] == target_id
    assert row["title"] == sample_download_row["title"]
    assert row["mediaType"] == sample_download_row["media_type"]
    assert row["orderNumber"] == sample_download_row["order_number"]

    assert "status" in row
    assert isinstance(row["status"], int)

    assert "statusMessage" in row
    assert isinstance(row["statusMessage"], str | None)

    assert "startTime" in row
    assert isinstance(row["startTime"], int)
    assert row["startTime"] == sample_download_row["start_time"]

    assert "endTime" in row
    assert isinstance(row["endTime"], int | None)

    assert "updateTime" in row
    assert isinstance(row["updateTime"], int | None)
