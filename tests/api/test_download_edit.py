import pytest
from scripts.media_server.src.constants import MediaType

from ..conftest import API_BULK_EDIT, API_GET_DOWNLOADS


def test_invalid_scenarios(client, auth_headers, seed):
    seed([{"id": 1}])

    # Wrong data type
    res = client.patch(
        API_BULK_EDIT, headers=auth_headers, json={"id": 1, "title": "Not a list"}
    )
    assert res.status_code == 400
    data = res.get_json()
    assert not data["status"]
    assert "Payload must be a list" in data["error"]

    # Invalid ID
    res = client.patch(
        API_BULK_EDIT, headers=auth_headers, json=[{"title": "No ID here"}]
    )
    data = res.get_json()
    assert not data["status"]
    assert data["data"][0]["error"] == "Missing 'id' field"

    # Invalid media type
    res = client.patch(
        API_BULK_EDIT, headers=auth_headers, json=[{"id": 1, "mediaType": -1}]
    )
    data = res.get_json()
    assert not data["status"]
    assert "Invalid mediaType" in data["data"][0]["error"]

    # No field passed
    res = client.patch(API_BULK_EDIT, headers=auth_headers, json=[{"id": 1}])
    data = res.get_json()
    assert not data["status"]
    assert data["data"][0]["error"] == "No fields to update"


@pytest.mark.parametrize(
    "test_name, seed_data, payload, expected_results",
    [
        (
            "single_valid",
            [{"id": 1, "title": "Old"}],
            [{"id": 1, "title": "Updated"}],
            [{"id": 1, "status": True}],
        ),
        (
            "multiple_valid",
            [{"id": 1}, {"id": 2}, {"id": 3}],
            [
                {"id": 1, "title": "One"},
                {"id": 2, "mediaType": MediaType.VIDEO},
                {"id": 3, "title": "Three", "mediaType": MediaType.GALLERY},
            ],
            [
                {"id": 1, "status": True},
                {"id": 2, "status": True},
                {"id": 3, "status": True},
            ],
        ),
        (
            "mixed_status",
            [{"id": 1}, {"id": 2}],
            [
                {"id": 1, "title": "Ok"},
                {"id": 2, "title": "Ok Too"},
                {"id": 99, "title": "I don't exist"},
            ],
            [
                {"id": 1, "status": True},
                {"id": 2, "status": True},
                {"id": 99, "status": False, "error": "not found"},
            ],
        ),
    ],
    ids=lambda x: x if isinstance(x, str) else "",
)
def test_valid_scenarios(
    test_name, seed_data, payload, expected_results, client, auth_headers, seed
):
    seed(seed_data)

    res = client.patch(API_BULK_EDIT, headers=auth_headers, json=payload)
    data = res.get_json()

    assert res.status_code == 200
    assert data["status"] is True
    assert len(data["data"]) == len(expected_results)

    for i, expected in enumerate(expected_results):
        actual = data["data"][i]

        assert actual["data"] == expected["id"]
        assert actual["status"] == expected["status"]

        if not expected["status"]:
            assert expected["error"].lower() in actual["error"].lower()


@pytest.mark.parametrize(
    "test_name, payload, new_title, new_media_type",
    [
        (
            "update_both",
            {"title": "New Title", "mediaType": MediaType.GALLERY},
            "New Title",
            MediaType.GALLERY,
        ),
        # Partial updates
        ("update_title", {"title": "New Title"}, "New Title", MediaType.IMAGE),
        (
            "update_media_type",
            {"mediaType": MediaType.VIDEO},
            "Test Page",
            MediaType.VIDEO,
        ),
        # Resetting
        ("reset_both", {"title": None, "mediaType": None}, None, None),
        ("reset_title", {"title": None}, None, MediaType.IMAGE),
        ("reset_media_type", {"mediaType": None}, "Test Page", None),
    ],
    ids=lambda x: x if isinstance(x, str) else "",
)
def test_bulk_edit_persistence(
    test_name,
    payload,
    new_title,
    new_media_type,
    client,
    auth_headers,
    seed,
    sample_download_row,
):
    """Test that rows are updated in the database."""
    seeded_rows = seed([sample_download_row])
    target_id = seeded_rows[0].id

    res = client.patch(
        API_BULK_EDIT, headers=auth_headers, json=[{"id": target_id, **payload}]
    )
    data = res.get_json()
    assert data["status"]
    assert data["data"][0]["status"]

    history_after = client.get(API_GET_DOWNLOADS, headers=auth_headers).json
    assert len(history_after) == 1

    updated_row = history_after[0]
    assert updated_row["title"] == new_title
    assert updated_row["mediaType"] == new_media_type

    assert "updateTime" in updated_row
    assert updated_row["updateTime"] is not None
    assert isinstance(updated_row["updateTime"], int)

    # Other data shouldn't be affected
    assert updated_row["orderNumber"] == sample_download_row["order_number"]
