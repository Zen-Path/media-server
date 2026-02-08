import pytest
from scripts.media_server.app.constants import MediaType

from ..conftest import API_BULK_EDIT, API_GET_DOWNLOADS


@pytest.mark.parametrize(
    "payload, error_msg",
    [
        (
            {"id": 1},
            "Invalid input type",
        ),
        (
            [{"title": "Test"}],
            "missing data for required field",
        ),
        (
            [{"id": None}],
            "field may not be null",
        ),
        (
            [{"id": "123"}],
            "not a valid integer",
        ),
        (
            [{"id": 1, "title": 123}],
            "not a valid string",
        ),
        (
            [{"id": 1, "mediaType": "123"}],
            "not a valid integer",
        ),
        (
            [{"id": 1, "status": "123"}],
            "not a valid integer",
        ),
    ],
    ids=[
        "not_a_list",
        "missing_id",
        "id_none",
        "id_wrong_type",
        "title_wrong_type",
        "media_type_wrong_type",
        "status_wrong_type",
    ],
)
def test_invalid_scenarios(payload, error_msg, client, auth_headers, seed):
    seed([{"id": 1}])

    res = client.patch(API_BULK_EDIT, headers=auth_headers, json=payload)
    assert res.status_code == 400

    data = res.get_json()
    assert not data["status"]
    assert error_msg.lower() in data["error"].lower()


@pytest.mark.parametrize(
    "seed_data, payload, expected_results",
    [
        (
            [{"id": 1, "title": "Old"}],
            [{"id": 1, "title": "New"}],
            [{"id": 1, "status": True, "updates": {"title": "New"}}],
        ),
        (
            [{"id": 1}, {"id": 2}, {"id": 3}],
            [
                {"id": 1, "title": "One"},
                {"id": 2, "mediaType": MediaType.VIDEO},
                {"id": 3, "title": "Three", "mediaType": MediaType.GALLERY},
            ],
            [
                {"id": 1, "status": True, "updates": {"title": "One"}},
                {"id": 2, "status": True, "updates": {"mediaType": MediaType.VIDEO}},
                {
                    "id": 3,
                    "status": True,
                    "updates": {"title": "Three", "mediaType": MediaType.GALLERY},
                },
            ],
        ),
        (
            [{"id": 1}, {"id": 2}],
            [
                {"id": 1, "title": "Ok"},
                {"id": 2, "title": "Ok Too"},
                {"id": 99, "title": "I don't exist"},
            ],
            [
                {"id": 1, "status": True, "updates": {"title": "Ok"}},
                {"id": 2, "status": True, "updates": {"title": "Ok Too"}},
                {"id": 99, "status": False, "updates": None, "error": "not found"},
            ],
        ),
        (
            [{"id": 1}],
            [{"id": 1}],
            [{"id": 1, "status": True, "error": None, "updates": {}}],
        ),
        (
            [{"id": 1}],
            [{"id": 1, "mediaType": 1}],
            [{"id": 1, "status": True, "error": None, "updates": {"mediaType": 1}}],
        ),
    ],
    ids=[
        "single_valid",
        "multiple_valid",
        "mixed_status",
        "no_field_to_update",
        "media_type_none",
    ],
)
def test_valid_scenarios(
    seed_data, payload, expected_results, client, auth_headers, seed
):
    seed(seed_data)

    res = client.patch(API_BULK_EDIT, headers=auth_headers, json=payload)
    assert res.status_code == 200

    data = res.get_json()
    assert data["status"]
    assert len(data["data"]) == len(expected_results)

    for i, expected in enumerate(expected_results):
        actual = data["data"][i]

        assert actual["id"] == expected["id"]
        assert actual["status"] == expected["status"]

        if not expected["status"]:
            assert expected["error"].lower() in actual["error"].lower()

        if "updates" in actual:
            assert actual["updates"] == expected["updates"]


@pytest.mark.parametrize(
    "payload, new_title, new_media_type",
    [
        (
            {"title": "New Title", "mediaType": MediaType.GALLERY},
            "New Title",
            MediaType.GALLERY,
        ),
        # Partial updates
        ({"title": "New Title"}, "New Title", MediaType.IMAGE),
        (
            {"mediaType": MediaType.VIDEO},
            "Test Page",
            MediaType.VIDEO,
        ),
        # Resetting
        ({"title": None, "mediaType": None}, None, None),
        ({"title": None}, None, MediaType.IMAGE),
        ({"mediaType": None}, "Test Page", None),
    ],
    ids=[
        "update_both",
        "update_title",
        "update_media_type",
        "reset_both",
        "reset_title",
        "reset_media_type",
    ],
)
def test_bulk_edit_persistence(
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
    print(history_after)
    assert len(history_after["data"]) == 1

    updated_row = history_after["data"][0]
    assert updated_row["title"] == new_title
    assert updated_row["mediaType"] == new_media_type

    assert "updateTime" in updated_row
    assert updated_row["updateTime"] is not None
    assert isinstance(updated_row["updateTime"], int)

    # Other data shouldn't be affected
    assert updated_row["orderNumber"] == sample_download_row["order_number"]
