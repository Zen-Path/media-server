import re

import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.ui


@pytest.fixture
def sort_data(mock_downloads):
    data = [
        {
            "id": 10,
            "mediaType": 2,
            "title": "Zebra",
            "status": 0,
            "startTime": "2026-01-01T10:00:00Z",
        },
        {
            "id": 1,
            "mediaType": 0,
            "title": "Apple",
            "status": 2,
            "startTime": "2026-01-01T12:00:00Z",
        },
        {
            "id": 5,
            "mediaType": 1,
            "title": "Mango",
            "status": 1,
            "startTime": "2026-01-01T11:00:00Z",
        },
    ]
    mock_downloads(data)
    return data


def test_id_sorting(dashboard, sort_data):
    dashboard.navigate()

    dashboard.table_header.locator(dashboard.h_col_id).click()
    expect(dashboard.get_sort_indicator(dashboard.h_col_id)).to_have_class(
        re.compile(r"fa-sort-up|fa-caret-up")
    )

    ids = dashboard.get_column_values(dashboard.b_col_id)
    assert ids == ["#1", "#5", "#10"]

    dashboard.table_header.locator(dashboard.h_col_id).click()
    expect(dashboard.get_sort_indicator(dashboard.h_col_id)).to_have_class(
        re.compile(r"fa-sort-down|fa-caret-down")
    )

    ids_desc = dashboard.get_column_values(dashboard.b_col_id)
    assert ids_desc == ["#10", "#5", "#1"]


def test_name_title_sorting(dashboard, sort_data):
    dashboard.navigate()

    dashboard.table_header.locator(dashboard.h_col_name).click()

    titles = dashboard.get_column_values(dashboard.b_col_title)
    assert titles == ["Apple", "Mango", "Zebra"]


def test_status_sorting(dashboard, sort_data):
    dashboard.navigate()

    dashboard.table_header.locator(dashboard.h_col_status).click()

    statuses = dashboard.get_column_values(dashboard.b_col_status_label)
    assert statuses == ["Pending", "In Progress", "Completed"]


def test_checkbox_sorting(page, dashboard, sort_data):
    """Verify that checked items can be moved to the top/bottom."""
    dashboard.navigate()

    dashboard.rows.nth(1).locator(dashboard.cell_checkbox).check()

    dashboard.table_header.locator(".col-checkbox").click()
    expect(dashboard.rows.last.locator(dashboard.b_col_title)).to_have_text("Apple")

    dashboard.table_header.locator(".col-checkbox").click()
    expect(dashboard.rows.first.locator(dashboard.b_col_title)).to_have_text("Apple")


def test_actions_column_is_not_sortable(dashboard, sort_data):
    dashboard.navigate()

    actions_header = dashboard.table_header.locator(".col-actions")

    # It should not have the .sortable class
    expect(actions_header).not_to_have_class(re.compile(r"sortable"))

    # Clicking it should do nothing to the row order
    initial_ids = dashboard.get_column_values(dashboard.b_col_id)
    actions_header.click()
    assert dashboard.get_column_values(dashboard.b_col_id) == initial_ids
