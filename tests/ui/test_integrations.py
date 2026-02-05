import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.ui


@pytest.fixture
def multi_data(mock_downloads):
    """Dataset with overlapping names for filtering and sorting."""
    data = [
        {"id": 10, "title": "Linux Tutorial (Advanced)", "url": "https://z.com/linux"},
        {"id": 1, "title": "Linux Tutorial (Basics)", "url": "https://a.com/linux"},
        {"id": 5, "title": "Windows Guide", "url": "https://m.com/win"},
        {"id": 20, "title": "Linux Tutorial (Network)", "url": "https://m.com/linux"},
    ]
    mock_downloads(data)
    return data


def test_filter_then_sort(dashboard, multi_data):
    dashboard.navigate()

    dashboard.filter_for("Linux")

    expect(dashboard.rows.filter(visible=True)).to_have_count(3)
    expect(dashboard.row_by_title("Windows Guide")).to_be_hidden()

    dashboard.table_header.locator(dashboard.h_col_id).click()

    visible_ids = [
        row.locator(dashboard.b_col_id).inner_text()
        for row in dashboard.rows.all()
        if row.is_visible()
    ]
    assert visible_ids == ["#1", "#10", "#20"]

    dashboard.table_header.locator(dashboard.h_col_name).click()

    visible_titles = [
        row.locator(dashboard.b_col_title).inner_text()
        for row in dashboard.rows.all()
        if row.is_visible()
    ]
    assert visible_titles == [
        "Linux Tutorial (Advanced)",
        "Linux Tutorial (Basics)",
        "Linux Tutorial (Network)",
    ]

    expect(dashboard.row_by_title("Windows Guide")).to_be_hidden()
