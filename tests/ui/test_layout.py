import re

import pytest
from playwright.sync_api import Page, expect


def test_static_elements_presence(dashboard, mock_downloads):
    """Verify that all global UI controls are present."""
    mock_downloads([])
    dashboard.navigate()

    expect(dashboard.search_input).to_be_visible()
    expect(dashboard.clear_btn).to_be_attached()
    expect(dashboard.theme_toggle).to_be_visible()
    expect(dashboard.table_info_btn).to_be_visible()
    expect(dashboard.footer).to_be_visible()


@pytest.mark.parametrize(
    "col_selector, expected_label",
    [
        ("h_col_id", "ID"),
        ("h_col_media", "Media Type"),
        ("h_col_name", "Name"),
        ("h_col_start_time", "Start Time"),
        ("h_col_status", "Status"),
    ],
)
def test_header_column_presence_and_tooltips(
    dashboard, mock_downloads, col_selector, expected_label
):
    mock_downloads([])
    dashboard.navigate()

    header_cell = dashboard.table_header.locator(getattr(dashboard, col_selector))
    expect(header_cell).to_be_visible()
    expect(header_cell).to_contain_text(expected_label)

    container = header_cell.locator(dashboard.icon_label_container)

    assert container.get_attribute("title") == expected_label


def test_header_checkbox_default_state(dashboard, mock_downloads):
    """Checkbox must exist and be unchecked by default."""
    mock_downloads([])
    dashboard.navigate()

    checkbox = dashboard.table_header.locator(dashboard.h_checkbox)
    expect(checkbox).to_be_visible()
    expect(checkbox).not_to_be_checked()


def test_body_checkbox_default_state(dashboard, mock_downloads):
    """Checkboxes must exist and be unchecked by default."""
    mock_downloads([{"id": 1}])
    dashboard.navigate()

    checkbox = dashboard.rows.first.locator(dashboard.cell_checkbox)
    expect(checkbox).to_be_visible()
    expect(checkbox).not_to_be_checked()


def test_url_opening_new_window(page: Page, dashboard, mock_downloads):
    """Clicking the name link should open the URL in a new tab."""
    target_url = "https://example.com/unique-path"
    mock_downloads([{"id": 1, "url": target_url, "title": "Click Me"}])
    dashboard.navigate()

    with page.expect_popup() as popup_info:
        dashboard.rows.first.locator(dashboard.b_col_name_link).click()

    new_page = popup_info.value
    assert new_page.url == target_url


def test_theme_toggle_cycles_state(page: Page, dashboard, mock_downloads):
    """
    Verify that clicking the toggle flips the dark-mode class regardless of starting
    state.
    """
    mock_downloads([])
    dashboard.navigate()

    body = page.locator("body")
    initial_is_dark = "dark-mode" in (body.get_attribute("class") or "")

    dashboard.theme_toggle.click()

    if initial_is_dark:
        expect(body).not_to_have_class(re.compile(r"dark-mode"))
    else:
        expect(body).to_have_class(re.compile(r"dark-mode"))

    # Click again to return to original state
    dashboard.theme_toggle.click()
    if initial_is_dark:
        expect(body).to_have_class(re.compile(r"dark-mode"))
    else:
        expect(body).not_to_have_class(re.compile(r"dark-mode"))


def test_theme_preference_persistence_on_reload(page: Page, dashboard, mock_downloads):
    """Verify that the theme selection survives a page refresh."""
    mock_downloads([])
    dashboard.navigate()

    body = page.locator("body")

    # If it's not dark, make it dark.
    if "dark-mode" not in (body.get_attribute("class") or ""):
        dashboard.theme_toggle.click()

    expect(body).to_have_class(re.compile(r"dark-mode"))

    page.reload()
    mock_downloads([])

    expect(body).to_have_class(re.compile(r"dark-mode"))
