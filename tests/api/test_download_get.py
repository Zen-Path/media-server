from app.constants import API_DOWNLOADS


def test_empty_return(client, auth_headers):
    """Test that an empty list is returned when there are no downloads."""
    response = client.get(API_DOWNLOADS, headers=auth_headers)
    assert response.status_code == 200

    resp_data = response.json
    assert resp_data["error"] is None
    assert len(resp_data["data"]) == 0


def test_get_all_downloads(client, auth_headers, seed, sample_download_row):
    """Test that all rows from the database are returned when no IDs are specified."""
    second_row = sample_download_row.copy()
    second_row["title"] = "Second Download"
    seeded_rows = seed([sample_download_row, second_row])

    response = client.get(API_DOWNLOADS, headers=auth_headers)
    assert response.status_code == 200

    data = response.json["data"]
    assert len(data) == len(seeded_rows)


def test_download_response_structure(client, auth_headers, seed, sample_download_row):
    """
    Test that the returned download object contains the expected fields and data types.
    """
    seeded_rows = seed([sample_download_row])
    target_id = seeded_rows[0].id

    response = client.get(API_DOWNLOADS, headers=auth_headers)
    assert response.status_code == 200

    data = response.json["data"]
    assert len(data) == len(seeded_rows)
    row = data[0]

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


def test_get_downloads_by_single_id(client, auth_headers, seed, sample_download_row):
    """Test fetching a specific download by a single ID."""
    seeded_rows = seed([sample_download_row])
    target_id = seeded_rows[0].id

    response = client.get(f"{API_DOWNLOADS}?ids={target_id}", headers=auth_headers)
    assert response.status_code == 200

    data = response.json["data"]
    assert len(data) == len(seeded_rows)
    assert data[0]["id"] == target_id


def test_get_downloads_by_multiple_ids(client, auth_headers, seed, sample_download_row):
    """Test fetching multiple specific downloads by a comma-separated list of IDs."""
    second_row = sample_download_row.copy()
    second_row["title"] = "Second Download"

    seeded_rows = seed([sample_download_row, second_row])
    id_1 = seeded_rows[0].id
    id_2 = seeded_rows[1].id

    response = client.get(f"{API_DOWNLOADS}?ids={id_1},{id_2}", headers=auth_headers)
    assert response.status_code == 200

    data = response.json["data"]
    assert len(data) == len(seeded_rows)

    returned_ids = [row["id"] for row in data]
    assert id_1 in returned_ids
    assert id_2 in returned_ids


def test_get_downloads_ignores_unknown_params(
    client, auth_headers, seed, sample_download_row
):
    """Test that undefined query parameters are safely ignored."""
    seeded_rows = seed([sample_download_row])
    target_id = seeded_rows[0].id

    # We pass 'foo=bar' and 'sort=asc' which are not defined in GetDownloadsQuerySchema
    response = client.get(
        f"{API_DOWNLOADS}?ids={target_id}&foo=bar&sort=asc", headers=auth_headers
    )

    assert response.status_code == 200

    data = response.json["data"]
    assert len(data) == len(seeded_rows)
    assert data[0]["id"] == target_id


def test_get_download_not_found(client, auth_headers):
    """Test that a 404 is returned if exactly one ID is requested but does not exist."""
    response = client.get(f"{API_DOWNLOADS}?ids=9999", headers=auth_headers)
    assert response.status_code == 404
    assert response.json["error"] is not None


def test_get_downloads_invalid_ids_format(client, auth_headers):
    """Test that a 400 is returned if the IDs are not valid integers."""
    response = client.get(f"{API_DOWNLOADS}?ids=1,abc,3", headers=auth_headers)
    assert response.status_code == 400
    assert response.json["error"] is not None
