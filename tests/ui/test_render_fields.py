import re

import pytest
from playwright.sync_api import expect
from scripts.media_server.src.constants import DownloadStatus, MediaType

pytestmark = pytest.mark.ui

# IDs


@pytest.mark.parametrize("input_id", [None, "", "123", "not-a-number"])
def test_id_invalid(dashboard, mock_downloads, input_id):
    """
    Invalid IDs means the UI should not render the row at all.
    """
    mock_downloads([{"id": input_id}])
    dashboard.navigate()

    assert dashboard.rows.count() == 0


@pytest.mark.parametrize("input_id", [0, 1, 12345])
def test_id_valid(dashboard, mock_downloads, input_id):
    """Valid IDs should render with a hash prefix."""
    mock_downloads([{"id": input_id}])
    dashboard.navigate()

    expect(dashboard.rows).to_have_count(1)
    expect(dashboard.rows.first.locator(dashboard.b_col_id)).to_have_text(
        f"#{input_id}"
    )


# Media Type


@pytest.mark.parametrize("media_id", [None, -1, 999, "unknown"])
def test_media_type_invalid(dashboard, mock_downloads, media_id):
    """Verify that unrecognized media types fallback to the 'Unknown' config."""
    mock_downloads([{"id": 1, "mediaType": media_id}])
    dashboard.navigate()

    expect(dashboard.rows.first.locator(dashboard.b_col_media_label)).to_have_text(
        "Unknown"
    )
    expect(dashboard.rows.first.locator(dashboard.b_col_media_container)).to_have_class(
        "icon-label-group type-unknown"
    )
    expect(dashboard.rows.first.locator(dashboard.b_col_media_icon)).to_have_class(
        "fa-solid fa-circle-question"
    )


@pytest.mark.parametrize(
    "media_id, expected_label, expected_class, expected_icon",
    [
        (MediaType.GALLERY, "Gallery", "type-gallery", "fa-layer-group"),
        (MediaType.VIDEO, "Video", "type-video", "fa-film"),
    ],
)
def test_media_type_valid(
    dashboard,
    mock_downloads,
    media_id,
    expected_label,
    expected_class,
    expected_icon,
):
    """Verify standard media types render correct label, class, and icon."""
    mock_downloads([{"id": 1, "mediaType": media_id}])
    dashboard.navigate()

    container = dashboard.rows.first.locator(dashboard.b_col_media_container)
    expect(container).to_have_class(f"icon-label-group {expected_class}")

    expect(dashboard.rows.first.locator(dashboard.b_col_media_label)).to_have_text(
        expected_label
    )
    expect(dashboard.rows.first.locator(dashboard.b_col_media_icon)).to_have_class(
        f"fa-solid {expected_icon}"
    )


# Title


@pytest.mark.parametrize("input_title", [None, "", 123])
def test_title_invalid(dashboard, mock_downloads, input_title):
    mock_downloads([{"id": 1, "title": input_title}])
    dashboard.navigate()

    title_el = dashboard.rows.first.locator(dashboard.b_col_title)
    expect(title_el).to_have_text("Untitled")


@pytest.mark.parametrize(
    "input_title",
    [
        "Standard Title",
        "0",
        "123",
        "Title with 'quotes' and \"double\"",
        "Rocket 🚀 & Unicode ℵ",
        "عنوان باللغة العربية",
        "A" * 300,
    ],
)
def test_title_valid(dashboard, mock_downloads, input_title):
    mock_downloads([{"id": 1, "title": input_title}])
    dashboard.navigate()

    title_el = dashboard.rows.first.locator(dashboard.b_col_title)
    expect(title_el).to_have_text(input_title)

    assert title_el.get_attribute("title") == input_title


def test_title_visual_truncation(dashboard, mock_downloads):
    """Verify that a super long title actually triggers the CSS truncation."""
    long_title = "Really long title " * 10
    mock_downloads([{"id": 1, "title": long_title}])
    dashboard.navigate()

    title_el = dashboard.rows.first.locator(dashboard.b_col_title)
    expect(title_el).to_have_class(re.compile(r"truncate"))
    assert dashboard.is_truncated(title_el), "Long title did not visually truncate"


# Start Time


@pytest.mark.parametrize(
    "input_date",
    [
        None,
        0,
        1769374602,
        "",
        "2026-01-25T20:00:00"  # No 'Z' at the end
        "2026-13-25T20:00:00Z",  # 13 months
    ],
)
def test_start_time_invalid(dashboard, mock_downloads, input_date):
    """Check how UI handles 'trash' in the date fields."""
    mock_downloads([{"id": 1, "startTime": input_date}])
    dashboard.navigate()

    date_el = dashboard.rows.first.locator(dashboard.b_col_start_time)
    expect(date_el).to_have_text("-")


@pytest.mark.parametrize(
    "start_time, end_time, expected_pattern",
    [
        # Finished
        (
            "2026-01-25T20:00:00Z",
            "2026-01-25T20:00:05Z",
            r"Finished at .* \(took \d+s\)",
        ),
        # Running
        ("2026-01-25T20:00:00Z", None, r"Download started more than .* ago"),
    ],
)
def test_start_time_tooltips(
    dashboard, mock_downloads, start_time, end_time, expected_pattern
):
    mock_downloads(
        [
            {
                "id": 1,
                "startTime": start_time,
                "endTime": end_time,
            }
        ]
    )
    dashboard.navigate()

    time_cell = dashboard.rows.first.locator(dashboard.b_col_start_time)
    tooltip = time_cell.get_attribute("title")

    assert re.match(expected_pattern, tooltip)


def test_start_time_valid(dashboard, mock_downloads):
    mock_downloads([{"id": 1, "startTime": "2026-01-25T20:00:05Z"}])
    dashboard.navigate()

    time_cell = dashboard.rows.first.locator(dashboard.b_col_start_time)
    expect(time_cell).to_have_text(re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"))


# Status


def test_status_invalid(dashboard, mock_downloads):
    """Fallback for invalid status integers."""
    mock_downloads([{"id": 1, "status": 999}])
    dashboard.navigate()

    expect(dashboard.rows.first.locator(dashboard.b_col_status_label)).to_have_text(
        "Unknown"
    )
    expect(
        dashboard.rows.first.locator(dashboard.b_col_status_container)
    ).to_have_class("icon-label-group text-muted")


@pytest.mark.parametrize(
    "status_int, expected_label, expected_color, expected_icon",
    [
        (DownloadStatus.DONE, "Completed", "text-success", "fa-check-circle"),
        (DownloadStatus.FAILED, "Failed", "text-danger", "fa-times-circle"),
    ],
)
def test_status_valid(
    dashboard,
    mock_downloads,
    status_int,
    expected_label,
    expected_color,
    expected_icon,
):
    """Verify download status renders correct text color and icon."""
    mock_downloads([{"id": 1, "status": status_int}])
    dashboard.navigate()

    container = dashboard.rows.first.locator(dashboard.b_col_status_container)
    expect(container).to_have_class(f"icon-label-group {expected_color}")

    expect(dashboard.rows.first.locator(dashboard.b_col_status_label)).to_have_text(
        expected_label
    )

    expect(dashboard.rows.first.locator(dashboard.b_col_status_icon)).to_have_class(
        re.compile(rf"{expected_icon}")
    )
