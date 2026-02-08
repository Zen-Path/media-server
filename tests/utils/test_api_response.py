import pytest
from scripts.media_server.app.utils.api_response import api_response


@pytest.mark.parametrize(
    "input_data, expected_data",
    [
        # Primitives & dicts
        ({"user_id": 1}, {"userId": 1}),
        ([{"a_b": 1}], [{"aB": 1}]),
        ({"meta_data": {"page_count": 10}}, {"metaData": {"pageCount": 10}}),
        # Mixed & complex lists
        (
            [{"user_info": {"first_name": "Alice"}}, "is_blacklisted"],
            [{"userInfo": {"firstName": "Alice"}}, "is_blacklisted"],
        ),
        # Empty & None
        ({}, {}),
        ([], []),
        (None, None),
    ],
    ids=["dict", "list", "nested", "complex_list", "empty_dict", "empty_list", "none"],
)
def test_api_response_data_formatting(input_data, expected_data):
    response, code = api_response(data=input_data)
    json_data = response.get_json()

    assert code == 200
    assert json_data["status"] is True
    assert json_data["data"] == expected_data


@pytest.mark.parametrize(
    "kwargs, expected_status, expected_code",
    [
        # Happy paths
        ({}, True, 200),
        ({"status_code": 201}, True, 201),
        # Infer False via error string
        ({"error": "Fail"}, False, 200),
        ({"error": "Fail", "status_code": 400}, False, 400),
        # Infer False via status code
        ({"status_code": 404}, False, 404),
        ({"status_code": 500}, False, 500),
        # Explicit status
        ({"error": "Warning", "status": True}, True, 200),
        ({"status": False}, False, 200),
        ({"status_code": 404, "status": True}, True, 404),
    ],
    ids=[
        "default_200",
        "created_201",
        "error_str_only",
        "error_str_with_400",
        "implicit_404_failure",
        "implicit_500_failure",
        "override_true_with_error",
        "override_false_on_success",
        "override_true_on_404",
    ],
)
def test_api_response_status_logic(kwargs, expected_status, expected_code):
    response, code = api_response(**kwargs)
    json_data = response.get_json()

    assert code == expected_code
    assert json_data["status"] is expected_status

    if "error" in kwargs:
        assert json_data["error"] == kwargs["error"]
