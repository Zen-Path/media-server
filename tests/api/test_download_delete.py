import pytest

from app.constants import API_DOWNLOADS


@pytest.mark.parametrize(
    "delete_ids, error_msg",
    [
        (None, "field may not be null."),
        ([], "Shorter than minimum length"),
        ("123", "Not a valid list"),
        (["123"], "Not a valid integer"),
    ],
)
def test_invalid_scenarios(delete_ids, error_msg, client, auth_headers):
    res = client.delete(API_DOWNLOADS, headers=auth_headers, json={"ids": delete_ids})
    assert res.status_code == 400

    data = res.get_json()
    assert not data["status"]
    assert data["data"] is None
    assert error_msg.lower() in data["error"].lower()


@pytest.mark.parametrize(
    "seed_ids, delete_ids, expected_items",
    [
        ([1], [1], [1]),
        ([1, 2, 3], [1, 2, 3], [1, 2, 3]),
        ([1], [1, 999], [1]),
        ([], [-1], []),
        ([], [888, 999], []),
        ([5], [5, 5], [5]),
    ],
    ids=[
        "single_valid",
        "all_valid",
        "mixed_status",
        "single_invalid",
        "all_invalid",
        "duplicates",
    ],
)
def test_valid_scenarios(
    seed_ids,
    delete_ids,
    expected_items,
    client,
    auth_headers,
    seed,
):
    seed([{"id": i} for i in seed_ids])

    res = client.delete(API_DOWNLOADS, headers=auth_headers, json={"ids": delete_ids})
    data = res.get_json()

    assert res.status_code == 200
    assert data["status"]
    assert data["data"]["ids"] == expected_items


def test_database_clearing(client, auth_headers, seed, sample_download_row):
    """Test that rows are removed from the database."""
    seeded_rows = seed([sample_download_row])
    target_id = seeded_rows[0].id

    res = client.delete(API_DOWNLOADS, headers=auth_headers, json={"ids": [target_id]})
    data = res.get_json()
    assert data["status"]

    history_after = client.get(API_DOWNLOADS, headers=auth_headers).json
    assert len(history_after["data"]) == 0
