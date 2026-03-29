"""Playwright fixtures for Flask dashboard tests."""
import socket
import threading
import time
from collections.abc import Generator

import pytest
from playwright.sync_api import Page

from yt_brain.web.dashboard import create_app


@pytest.fixture(scope="session")
def flask_server() -> Generator[str, None, None]:
    """Start Flask dashboard on a random port."""
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()

    app = create_app()
    thread = threading.Thread(
        target=lambda: app.run(host="127.0.0.1", port=port, use_reloader=False),
        daemon=True,
    )
    thread.start()
    time.sleep(0.5)
    yield f"http://127.0.0.1:{port}"


@pytest.fixture
def dashboard_page(page: Page, flask_server: str) -> Page:
    """Navigate to dashboard and return Playwright page."""
    page.goto(flask_server)
    return page
