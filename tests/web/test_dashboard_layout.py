"""Test dashboard layout stays within 1008x828 viewport."""

import pytest
from playwright.sync_api import Page, expect

VIEWPORT = {"width": 1008, "height": 828}


@pytest.fixture
def sized_page(page: Page, flask_server: str) -> Page:
    """Navigate to dashboard at the target viewport size."""
    page.set_viewport_size(VIEWPORT)
    page.goto(flask_server)
    page.wait_for_load_state("networkidle")
    return page


def _no_horizontal_overflow(page: Page) -> bool:
    """Check that no element's bounding box exceeds the viewport width."""
    return page.evaluate(
        """() => {
            const vw = window.innerWidth;
            if (document.body.scrollWidth > vw) return false;
            // Check the full-width card hasn't grown beyond its grid track
            const card = document.querySelector('.card.full-width');
            const grid = document.querySelector('.grid');
            if (card && grid) {
                const cardRight = card.getBoundingClientRect().right;
                const gridRight = grid.getBoundingClientRect().right;
                if (cardRight > gridRight + 1) return false;
            }
            // Check the video table isn't wider than its container
            const vl = document.querySelector('.video-list');
            if (vl) {
                const table = vl.querySelector('table');
                if (table && table.offsetWidth > vl.clientWidth + 1) return false;
            }
            return true;
        }"""
    )


def _overflow_debug(page: Page) -> str:
    """Return debug info about what's overflowing."""
    return page.evaluate(
        """() => {
            const vw = window.innerWidth;
            const card = document.querySelector('.card.full-width');
            const grid = document.querySelector('.grid');
            const vl = card?.querySelector('.video-list');
            const table = vl?.querySelector('table');
            return JSON.stringify({
                viewport: vw,
                body_scrollWidth: document.body.scrollWidth,
                grid_width: grid?.getBoundingClientRect().width,
                card_width: card?.getBoundingClientRect().width,
                card_right: card?.getBoundingClientRect().right,
                grid_right: grid?.getBoundingClientRect().right,
                videoList_clientWidth: vl?.clientWidth,
                table_offsetWidth: table?.offsetWidth,
            });
        }"""
    )


def test_initial_load_no_overflow(sized_page: Page):
    """Dashboard fits within 1008x828 on initial load."""
    assert _no_horizontal_overflow(sized_page), _overflow_debug(sized_page)


def test_channel_search_no_overflow(sized_page: Page):
    """Typing in the channel search bar must not cause layout overflow."""
    channel_input = sized_page.locator("#channelSearch")
    expect(channel_input).to_be_visible()

    for length in range(1, 21):
        text = "a" * length
        channel_input.fill(text)
        assert _no_horizontal_overflow(sized_page), (
            f"Overflow at {length} chars: {_overflow_debug(sized_page)}"
        )


def test_channel_search_with_spaces_no_overflow(sized_page: Page):
    """Typing 'web ' (with trailing space) must not cause layout overflow."""
    channel_input = sized_page.locator("#channelSearch")
    expect(channel_input).to_be_visible()

    test_strings = ["w", "we", "web", "web ", "web d", "web de", "web dev",
                    "web dev ", "web development"]
    for text in test_strings:
        channel_input.fill(text)
        assert _no_horizontal_overflow(sized_page), (
            f"Overflow at '{text}': {_overflow_debug(sized_page)}"
        )


def test_title_search_no_overflow(sized_page: Page):
    """Typing in the title search bar must not cause layout overflow."""
    title_input = sized_page.locator("#titleSearch")
    expect(title_input).to_be_visible()

    for length in range(1, 21):
        text = "a" * length
        title_input.fill(text)
        assert _no_horizontal_overflow(sized_page), (
            f"Overflow at {length} chars: {_overflow_debug(sized_page)}"
        )


def test_both_searches_filled_no_overflow(sized_page: Page):
    """Both search fields filled simultaneously must not overflow."""
    sized_page.locator("#titleSearch").fill("some long search term here")
    sized_page.locator("#channelSearch").fill("another long channel name")

    assert _no_horizontal_overflow(sized_page), _overflow_debug(sized_page)
