from typing import Any

import pytest
from playwright.sync_api import Page, expect

from app.constants import API_DOWNLOADS
from tests.ui.pages.dashboard_page import DashboardPage


@pytest.fixture(scope="session", autouse=True)
def configure_playwright_expect():
    expect.set_options(timeout=100)


@pytest.fixture
def dashboard(page: Page) -> DashboardPage:
    return DashboardPage(page)


@pytest.fixture
def mock_downloads(page: Page):
    """Returns a function that intercepts the GET downloads call."""

    def _mock(
        data: Any = None,
        error: str | None = None,
        status: bool = True,
    ):
        response = {
            "status": status,
            "data": data,
            "error": error,
        }
        page.route(
            f"**{API_DOWNLOADS}",
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                json=response,
            ),
        )

    return _mock
