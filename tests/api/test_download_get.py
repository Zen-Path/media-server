import pytest

from app.constants import API_DOWNLOADS
from app.schemas.download import DownloadSchema


def test_download_response_structure(client, auth_headers, seed, sample_download_row):
    """
    Test that the returned download object matches the schema and seeded data.
    """
    seeded_rows = seed([sample_download_row])
    target_id = seeded_rows[0].id

    response = client.get(API_DOWNLOADS, headers=auth_headers)
    assert response.status_code == 200

    data = response.json["data"]
    assert len(data) == len(seeded_rows)
    row = data[0]

    # Structure validation
    schema_errors = DownloadSchema().validate(row)
    assert not schema_errors, f"Response schema mismatch: {schema_errors}"

    # Content validation
    assert row["id"] == target_id
    assert row["title"] == sample_download_row["title"]


@pytest.mark.parametrize("item_count", [0, 1, 5])
def test_get_all_downloads(client, auth_headers, seed, sample_download_row, item_count):
    """Test that all rows from the database are returned and in the expected order."""
    rows_to_seed = [
        {**sample_download_row, "title": f"Item {i + 1}"} for i in range(item_count)
    ]
    seeded_rows = seed(rows_to_seed)

    response = client.get(API_DOWNLOADS, headers=auth_headers)

    assert response.status_code == 200
    resp_data = response.json
    assert resp_data["error"] is None

    returned_data = resp_data["data"]
    assert len(returned_data) == item_count

    if item_count > 0:
        expected_sorted_rows = sorted(seeded_rows, key=lambda x: x.id, reverse=True)
        expected_titles = [row.title for row in expected_sorted_rows]

        returned_titles = [item["title"] for item in returned_data]
        returned_ids = [item["id"] for item in returned_data]

        assert returned_ids == sorted(returned_ids, reverse=True), (
            "API did not return items in correct order"
        )
        assert returned_titles == expected_titles, (
            "API data content or order is incorrect"
        )


@pytest.mark.parametrize("id_count", [0, 1, 5])
def test_get_downloads_by_ids(
    client, auth_headers, seed, sample_download_row, id_count
):
    """Test fetching specific downloads by a comma-separated list of IDs."""
    # We add 2 extra "noise" rows to guarantee the API is actually filtering by ID
    noise_count = 2
    rows_to_seed = [
        {**sample_download_row, "title": f"Item {i + 1}"}
        for i in range(noise_count + id_count)
    ]
    seeded_rows = seed(rows_to_seed)

    seeded_rows = sorted(seeded_rows, key=lambda x: x.id, reverse=True)

    target_rows = seeded_rows[noise_count:] if id_count > 0 else []
    target_ids = [str(row.id) for row in target_rows]

    query_string = f"?ids={','.join(target_ids)}"
    response = client.get(f"{API_DOWNLOADS}{query_string}", headers=auth_headers)

    assert response.status_code == 200
    resp_data = response.json
    assert resp_data["error"] is None

    returned_data = resp_data["data"]

    # If id list is empty, the endpoint returns all available rows
    if id_count == 0:
        assert len(returned_data) == len(rows_to_seed)

    if id_count > 0:
        assert len(returned_data) == id_count

        expected_titles = [row.title for row in target_rows]

        returned_ids = [str(item["id"]) for item in returned_data]
        returned_titles = [item["title"] for item in returned_data]

        assert returned_ids == target_ids, "API did not return the exact requested IDs"
        assert returned_titles == expected_titles, (
            "API data content or order is incorrect"
        )


def test_get_downloads_invalid_ids_format(client, auth_headers):
    """Test that a 400 is returned if the IDs are not valid integers."""
    response = client.get(f"{API_DOWNLOADS}?ids=1,abc,3", headers=auth_headers)
    assert response.status_code == 400
    assert response.json["error"] is not None
