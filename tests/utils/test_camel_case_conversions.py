import pytest

from app.utils.tools import recursive_camelize, to_camel_case


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


@pytest.mark.parametrize(
    "payload, expected",
    [
        (
            {"user_id": 123, "first_name": "John", "is_active": True},
            {"userId": 123, "firstName": "John", "isActive": True},
        ),
        (
            [{"item_id": 1, "item_name": "A"}, {"item_id": 2, "item_name": "B"}],
            [{"itemId": 1, "itemName": "A"}, {"itemId": 2, "itemName": "B"}],
        ),
        (
            {
                "meta_data": {
                    "page_count": 5,
                    "current_page": 1,
                    "nested_list": [{"deep_key": "value"}],
                }
            },
            {
                "metaData": {
                    "pageCount": 5,
                    "currentPage": 1,
                    "nestedList": [{"deepKey": "value"}],
                }
            },
        ),
        # Primitives
        (["a", "b", "c"], ["a", "b", "c"]),
        ("just_a_string", "just_a_string"),
        (123, 123),
        (None, None),
        # Edge cases
        ({}, {}),
        ([], []),
    ],
    ids=[
        "simple_dict",
        "list_of_objects",
        "deep_recursion",
        "list_of_str",
        "number",
        "none",
        "simple_str",
        "empty_dict",
        "empty_list",
    ],
)
def test_recursive_camelize(payload, expected):
    assert recursive_camelize(payload) == expected
