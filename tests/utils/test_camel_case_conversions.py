import pytest
from scripts.media_server.app.utils.tools import recursive_camelize, to_camel_case


@pytest.mark.parametrize(
    "input_str, expected",
    [
        ("word", "word"),
        ("my_variable", "myVariable"),
        ("my_long_var", "myLongVar"),
        ("camelCase", "camelCase"),
        ("wEird_UsEr_ID", "weirdUserId"),
        # Keep as-is for idempotency (for already camelCase str)
        ("wEirdUsErID", "wEirdUsErID"),
        ("long___variable", "longVariable"),
        # Preserving leading & trailing underscores
        ("_private_var", "_privateVar"),
        ("class_", "class_"),
        ("__init__", "__init__"),
        # Edge cases
        ("_", "_"),
        ("__", "__"),
        ("", ""),
    ],
    ids=[
        "one_word",
        "two_words",
        "three_words",
        "alreadyCamelCase",
        "mixed_case",
        "mixed_case_no_underscores",
        "collapse_underscores",
        "leading_underscore",
        "trailing_underscore",
        "lead_and_trail_underscores",
        "one_underscore",
        "multiple_underscores",
        "empty",
    ],
)
def test_to_camel_case(input_str, expected):
    assert to_camel_case(input_str) == expected


def test_camelize_simple_dict():
    """Verify keys are transformed but values remain untouched."""
    payload = {"user_id": 123, "first_name": "John", "is_active": True}
    expected = {"userId": 123, "firstName": "John", "isActive": True}
    assert recursive_camelize(payload) == expected


def test_camelize_list_of_dicts():
    """Verify it handles lists of objects."""
    payload = [{"item_id": 1, "item_name": "A"}, {"item_id": 2, "item_name": "B"}]
    expected = [{"itemId": 1, "itemName": "A"}, {"itemId": 2, "itemName": "B"}]
    assert recursive_camelize(payload) == expected


def test_camelize_nested_dict():
    """Verify it recurses deep into dictionaries."""
    payload = {
        "meta_data": {
            "page_count": 5,
            "current_page": 1,
            "nested_list": [{"deep_key": "value"}],
        }
    }
    expected = {
        "metaData": {
            "pageCount": 5,
            "currentPage": 1,
            "nestedList": [{"deepKey": "value"}],
        }
    }
    assert recursive_camelize(payload) == expected


def test_camelize_mixed_types():
    """Verify it doesn't crash on primitives or lists of primitives."""
    # List of strings shouldn't change
    assert recursive_camelize(["a", "b", "c"]) == ["a", "b", "c"]

    # Primitives should pass through
    assert recursive_camelize(123) == 123
    assert recursive_camelize(None) is None
    assert recursive_camelize("just_a_string") == "just_a_string"


def test_camelize_edge_cases():
    """Verify empty structures."""
    assert recursive_camelize({}) == {}
    assert recursive_camelize([]) == []
