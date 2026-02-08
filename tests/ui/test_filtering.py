import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.ui


@pytest.fixture
def filter_items(mock_downloads):
    data = [
        {"id": 1, "title": "Alpha Video", "url": "https://a.com"},
        {"id": 2, "title": "Beta Movie", "url": "https://b.com"},
        {"id": 3, "title": "Gamma Clip", "url": "https://c.com"},
    ]
    mock_downloads(data)
    return data


def test_filter_filtering_visibility(page, dashboard, filter_items):
    """Verify rows hide/show as the user types sequentially."""
    dashboard.navigate()

    # Initially all visible
    expect(dashboard.rows).to_have_count(3)

    dashboard.filter_for("Video")

    expect(dashboard.row_by_title("Alpha Video")).to_be_visible()
    expect(dashboard.row_by_title("Beta Movie")).to_be_hidden()
    expect(dashboard.row_by_title("Gamma Clip")).to_be_hidden()

    # Editing the filter term
    for _ in range(3):
        dashboard.search_input.press("Backspace")

    expect(dashboard.row_by_title("Alpha Video")).to_be_visible(timeout=1000)
    expect(dashboard.row_by_title("Beta Movie")).to_be_visible(timeout=1000)
    expect(dashboard.row_by_title("Gamma Clip")).to_be_hidden(timeout=1000)


def test_filter_clear_flow(dashboard, filter_items):
    """Verify that the clear button resets visibility and its own state."""
    dashboard.navigate()

    # Input empty, button hidden
    expect(dashboard.clear_btn).to_be_hidden()

    # Button should appear immediately
    dashboard.filter_for("Gamma")
    expect(dashboard.clear_btn).to_be_visible()
    expect(dashboard.row_by_title("Alpha Video")).to_be_hidden()

    dashboard.clear_btn.click()

    # Result: Input cleared, button hidden, rows restored
    expect(dashboard.search_input).to_have_value("", timeout=1000)
    expect(dashboard.clear_btn).to_be_hidden(timeout=1000)
    expect(dashboard.row_by_title("Alpha Video")).to_be_visible(timeout=1000)
    expect(dashboard.rows.filter(visible=True)).to_have_count(3, timeout=1000)


@pytest.mark.parametrize(
    "query, expected_row_count",
    [
        ("MOVIE", 1),
        ("!!!??###🐍", 0),
        ("   Beta   ", 1),
        ("   ", 3),
    ],
    ids=[
        "case_insensitive",
        "special_chars",
        "untrimmed",
        "spaces_only",
    ],
)
def test_filter_query_variants(query, expected_row_count, dashboard, filter_items):
    dashboard.navigate()
    dashboard.filter_for(query)

    expect(dashboard.rows.filter(visible=True)).to_have_count(expected_row_count)

    if "MOVIE" in query.upper() or "BETA" in query.upper():
        expect(dashboard.row_by_title("Beta Movie")).to_be_visible()


def test_filter_hides_but_keeps_dom(dashboard, filter_items):
    dashboard.navigate()

    dashboard.filter_for("Python")

    alpha_row = dashboard.row_by_title("Alpha Video")
    expect(alpha_row).to_be_attached()

    # But it is not visible to the user
    expect(alpha_row).to_be_hidden()
