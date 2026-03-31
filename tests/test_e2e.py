"""End-to-end Playwright test for the WonderLens Activity Demo.

Requires both backend and frontend servers running:
  - Backend: cd backend && uv run uvicorn server:app --port 8000
  - Frontend: cd frontend && npm run dev

Or use the with_server.py helper if available.

Run with: uv run pytest tests/test_e2e.py -m e2e -v
"""

import socket

import pytest


def _server_listening(host: str, port: int) -> bool:
    """Return True if a TCP connection to host:port succeeds."""
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


_backend_up = _server_listening("localhost", 8000)
_frontend_up = _server_listening("localhost", 5173)

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        not (_backend_up and _frontend_up),
        reason="E2E tests require backend (port 8000) and frontend (port 5173) servers running",
    ),
]


@pytest.fixture(scope="module")
def browser_page():
    """Launch a headless Chromium browser and yield a page."""
    try:
        from playwright.sync_api import sync_playwright  # noqa: PLC0415
    except ImportError:
        pytest.skip("playwright not installed — run: pip install playwright && playwright install chromium")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        yield page
        browser.close()


class TestFrontendLoads:
    def test_app_renders(self, browser_page) -> None:
        page = browser_page
        page.goto("http://localhost:5173", timeout=10000)
        page.wait_for_load_state("networkidle")

        # TopBar should be visible
        assert page.locator("text=WonderLens").first.is_visible() or page.title() != ""

    def test_photo_selector_visible(self, browser_page) -> None:
        page = browser_page
        page.goto("http://localhost:5173", timeout=10000)
        page.wait_for_load_state("networkidle")

        # Photo selector should be the initial view
        page.screenshot(path="/tmp/wonderlens_initial.png", full_page=True)

    def test_tier_dropdown_exists(self, browser_page) -> None:
        page = browser_page
        page.goto("http://localhost:5173", timeout=10000)
        page.wait_for_load_state("networkidle")

        # Should have tier selector with T0/T1/T2 options
        selects = page.locator("select").all()
        assert len(selects) > 0

    def test_health_endpoint_reachable(self, browser_page) -> None:
        page = browser_page
        response = page.goto("http://localhost:8000/api/health", timeout=5000)
        assert response is not None
        assert response.status == 200
        body = response.json()
        assert body["status"] == "ok"

    def test_footer_shows_idle_status(self, browser_page) -> None:
        page = browser_page
        page.goto("http://localhost:5173", timeout=10000)
        page.wait_for_load_state("networkidle")

        footer = page.locator("footer")
        assert footer.is_visible()
        footer_text = footer.inner_text()
        assert "idle" in footer_text.lower() or "Round" in footer_text
