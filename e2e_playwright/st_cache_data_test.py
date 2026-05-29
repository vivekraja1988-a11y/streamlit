# Copyright (c) Streamlit Inc. (2018-2022) Snowflake Inc. (2022-2026)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import re

from playwright.sync_api import Locator, Page, expect

from e2e_playwright.conftest import ImageCompareFunction, rerun_app, wait_for_app_run
from e2e_playwright.shared.app_utils import (
    click_button,
    click_checkbox,
    get_button,
    get_element_by_key,
    get_image,
)


def test_that_caching_shows_cached_widget_warning(app: Page):
    click_button(app, "Run cached function with widget warning")
    wait_for_app_run(app)
    expect(app.get_by_test_id("stException")).to_have_count(1)

    exception_element = app.get_by_test_id("stException").nth(0)
    expect(exception_element).to_contain_text("CachedWidgetWarning: Your script uses")


def test_that_nested_cached_function_shows_cached_widget_warning(app: Page):
    click_button(app, "Run nested cached function with widget warning")
    expect(app.get_by_test_id("stException")).to_have_count(2)

    expect(app.get_by_test_id("stException").nth(0)).to_contain_text(
        "CachedWidgetWarning: Your script uses"
    )
    expect(app.get_by_test_id("stException").nth(1)).to_contain_text(
        "CachedWidgetWarning: Your script uses"
    )


def test_that_replay_element_works_as_expected(app: Page):
    click_button(app, "Cached function with element replay")
    expect(app.get_by_test_id("stException")).to_have_count(0)
    expect(app.get_by_text("Cache executions: 1")).to_be_visible()
    expect(app.get_by_text("Cache return 1")).to_be_visible()

    # Execute again, the values should be the same:
    click_button(app, "Cached function with element replay")
    expect(app.get_by_test_id("stException")).to_have_count(0)
    expect(app.get_by_text("Cache executions: 1")).to_be_visible()
    expect(app.get_by_text("Cache return 1")).to_be_visible()


# have 1 test so we don't have to reload the video
def test_st_audio_player_and_video_player(app: Page):
    audio = app.get_by_test_id("stAudio")

    expect(audio).to_be_visible()
    expect(audio).to_have_attribute("controls", "")
    expect(audio).to_have_attribute("src", re.compile(r"^.*\.wav$", re.IGNORECASE))
    audio_src = audio.get_attribute("src")

    video_player = app.get_by_test_id("stVideo")
    expect(video_player).to_be_visible()
    expect(video_player).to_have_attribute(
        "src", re.compile(r"^.*\.mp4$", re.IGNORECASE)
    )
    video_src = video_player.get_attribute("src")

    rerun_app(app)

    expect(audio).to_have_attribute("src", audio_src or "")
    expect(video_player).to_have_attribute("src", video_src or "")


def test_cached_image_replay(app: Page):
    """Test that the image is cached and replayed correctly."""
    image_element = get_image(app, "A black square").locator("img")
    # Image should be visible
    expect(image_element).to_be_visible()

    expect(image_element).to_have_css("height", "200px")
    expect(image_element).to_have_css("width", "200px")
    image_src = image_element.get_attribute("src")

    click_checkbox(app, "Show image")
    # Image should disappear
    expect(image_element).not_to_be_attached()

    click_checkbox(app, "Show image")
    # Image should be visible again
    expect(image_element).to_be_visible()
    expect(image_element).to_have_css("height", "200px")
    expect(image_element).to_have_css("width", "200px")
    expect(image_element).to_have_attribute("src", image_src or "")


def test_cached_code_replay(app: Page, assert_snapshot: ImageCompareFunction):
    """Test that the code is cached and replayed correctly with width and height."""
    code_element = app.get_by_test_id("stCode").first
    expect(code_element).to_be_visible()

    # Test dimensions with snapshots since the width/height is set on the element container.
    assert_snapshot(code_element, name="st_cache_data-st_code_before_caching")

    click_checkbox(app, "Show code")
    expect(code_element).not_to_be_attached()

    click_checkbox(app, "Show code")
    expect(code_element).to_be_visible()
    assert_snapshot(code_element, name="st_cache_data-st_code_after_caching")


# Regression tests for PR #14565 / issue #14555:
# The cache spinner overlay used to visually hide a leading st.progress bar.
# The PR fixes that by extending the spinner's paddingBottom and pulling the
# container up with a negative marginBottom. These tests assert that the fix
# works for the original case AND does not regress visuals for other common
# first elements raised in review (st.text, st.markdown, st.image).
#
# Note: we click via `get_button(...).click()` (not `click_button`) because
# `click_button` waits for the app run to finish, which would make the cache
# spinner disappear before we can observe it.


def _expect_cache_spinner_visible(container: Locator) -> None:
    """The cache spinner uses data-testid=stSpinner + class stCacheSpinner."""
    expect(container.locator(".stCacheSpinner")).to_be_visible()


def test_cache_spinner_does_not_hide_progress(
    app: Page, assert_snapshot: ImageCompareFunction
):
    """The cache spinner must not visually hide a leading st.progress bar."""
    get_button(app, "Run cache spinner over progress").click()

    container = get_element_by_key(app, "cache_overlap_progress_container")
    _expect_cache_spinner_visible(container)
    # The progress bar must remain visible while the cache spinner overlay is on.
    expect(container.get_by_test_id("stProgress")).to_be_visible()
    # Must NOT happen: a second (orphan) spinner re-rendered next to the progress.
    expect(container.get_by_test_id("stSpinner")).to_have_count(1)

    # Slightly relaxed image_threshold (1%) to absorb minor anti-aliasing /
    # spinner-icon rendering noise that the default 0.2% can flag as failure.
    assert_snapshot(
        container,
        name="st_cache_data-cache_spinner_over_progress",
        image_threshold=0.01,
    )


def test_cache_spinner_does_not_clip_text(
    app: Page, assert_snapshot: ImageCompareFunction
):
    """The cache spinner must not clip a short leading st.text."""
    get_button(app, "Run cache spinner over text").click()

    container = get_element_by_key(app, "cache_overlap_text_container")
    _expect_cache_spinner_visible(container)
    expect(container.get_by_text("hello", exact=True)).to_be_visible()

    assert_snapshot(
        container,
        name="st_cache_data-cache_spinner_over_text",
        image_threshold=0.01,
    )


def test_cache_spinner_does_not_clip_markdown_descenders(
    app: Page, assert_snapshot: ImageCompareFunction
):
    """The cache spinner gradient must not clip descenders in a heading."""
    get_button(app, "Run cache spinner over markdown").click()

    container = get_element_by_key(app, "cache_overlap_markdown_container")
    _expect_cache_spinner_visible(container)
    expect(container.get_by_role("heading", name="Heading pgjy")).to_be_visible()

    assert_snapshot(
        container,
        name="st_cache_data-cache_spinner_over_markdown",
        image_threshold=0.01,
    )


def test_cache_spinner_does_not_clip_image(
    app: Page, assert_snapshot: ImageCompareFunction
):
    """The cache spinner must not clip a leading st.image."""
    get_button(app, "Run cache spinner over image").click()

    container = get_element_by_key(app, "cache_overlap_image_container")
    _expect_cache_spinner_visible(container)
    expect(container.get_by_test_id("stImage")).to_be_visible()

    assert_snapshot(
        container,
        name="st_cache_data-cache_spinner_over_image",
        image_threshold=0.01,
    )
