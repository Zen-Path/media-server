import pytest
from playwright.sync_api import Page, expect
from scripts.media_server.tests.conftest import API_GET_DOWNLOADS
from scripts.media_server.tests.ui.pages.dashboard_page import DashboardPage


@pytest.fixture(scope="session", autouse=True)
def configure_playwright_expect():
    expect.set_options(timeout=100)


@pytest.fixture
def dashboard(page):
    return DashboardPage(page)


@pytest.fixture
def mock_downloads(page: Page):
    """Returns a function that intercepts the GET downloads call."""

    def _mock(data: list):
        page.route(
            f"**{API_GET_DOWNLOADS}",
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                json=data,
            ),
        )

    return _mock
