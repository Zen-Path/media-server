import pytest

from ..conftest import API_BULK_DELETE, API_GET_DOWNLOADS


def test_invalid_scenarios(client, auth_headers):
    # No IDs
    res = client.post(API_BULK_DELETE, headers=auth_headers, json={"ids": []})
    assert res.status_code == 400
    data = res.get_json()
    assert not data["status"]
    assert data["data"] is None
    assert data["error"] == "Invalid or empty 'ids' list"

    # One invalid ID
    res = client.post(API_BULK_DELETE, headers=auth_headers, json={"ids": [999]})
    data = res.get_json()
    assert res.status_code == 200
    assert not data["status"]
    assert data["data"][0]["error"] == "Record ID not found"


@pytest.mark.parametrize(
    "test_name, seed_ids, delete_ids, expected_overall, expected_items",
    [
        ("single_valid", [1], [1], True, [{"id": 1, "status": True}]),
        (
            "multiple_valid",
            [1, 2, 3],
            [1, 2, 3],
            True,
            [
                {"id": 1, "status": True},
                {"id": 2, "status": True},
                {"id": 3, "status": True},
            ],
        ),
        (
            "mixed_status",
            [1],
            [1, 999],
            True,
            [{"id": 1, "status": True}, {"id": 999, "status": False}],
        ),
        (
            "all_missing",
            [],
            [888, 999],
            False,
            [{"id": 888, "status": False}, {"id": 999, "status": False}],
        ),
        ("duplicates", [5], [5, 5], True, [{"id": 5, "status": True}]),
    ],
    ids=lambda x: x if isinstance(x, str) else "",
)
def test_valid_scenarios(
    test_name,
    seed_ids,
    delete_ids,
    expected_overall,
    expected_items,
    client,
    auth_headers,
    seed,
):
    seed([{"id": i} for i in seed_ids])

    res = client.post(API_BULK_DELETE, headers=auth_headers, json={"ids": delete_ids})
    data = res.get_json()
    print(data)

    assert res.status_code == 200
    assert data["status"] == expected_overall
    assert len(data["data"]) == len(expected_items)

    for i, expected in enumerate(expected_items):
        actual = data["data"][i]

        assert actual["data"] == expected["id"]
        assert actual["status"] == expected["status"]


def test_database_clearing(client, auth_headers, seed, sample_download_row):
    """Test that rows are removed from the database."""
    seeded_rows = seed([sample_download_row])
    target_id = seeded_rows[0].id

    res = client.post(API_BULK_DELETE, headers=auth_headers, json={"ids": [target_id]})
    data = res.get_json()
    assert data["status"]

    history_after = client.get(API_GET_DOWNLOADS, headers=auth_headers).json
    assert len(history_after) == 0
