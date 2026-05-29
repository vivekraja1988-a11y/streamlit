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

import time
from typing import TYPE_CHECKING, cast

import numpy as np
import requests

import streamlit as st

if TYPE_CHECKING:
    import numpy.typing as npt


@st.cache_data
def with_cached_widget_warning():
    st.write("Cached function that should show a widget usage warning.")
    st.selectbox("selectbox", ["foo", "bar", "baz", "qux"], index=1)


if st.button("Run cached function with widget warning"):
    with_cached_widget_warning()


@st.cache_data
def inner_cache_function():
    st.radio("radio 2", ["foo", "bar", "baz", "qux"], index=1)


@st.cache_data
def nested_cached_function():
    inner_cache_function()
    st.selectbox("selectbox 2", ["foo", "bar", "baz", "qux"], index=1)


if st.button("Run nested cached function with widget warning"):
    # When running nested_cached_function(), we get two warnings, one from
    # nested_cached_function() and one from inner_cache_function.
    nested_cached_function()


if "run_counter" not in st.session_state:
    st.session_state.run_counter = 0


@st.cache_data
def replay_element() -> int:
    st.session_state.run_counter += 1
    st.markdown(f"Cache executions: {st.session_state.run_counter}")
    return cast("int", st.session_state.run_counter)


if st.button("Cached function with element replay"):
    st.write("Cache return", replay_element())


@st.cache_data
def audio():
    url = "https://www.w3schools.com/html/horse.ogg"
    file = requests.get(url).content
    st.audio(file)


@st.cache_data
def video():
    url = "https://www.w3schools.com/html/mov_bbb.mp4"
    file = requests.get(url).content
    st.video(file)


@st.cache_data
def code():
    st.code("print('Hello, world!')", width=300, height=200)


audio()
video()

if st.checkbox("Show code", True):
    code()


@st.cache_data
def image():
    img: npt.NDArray[np.int64] = np.repeat(0, 10000).reshape(100, 100)
    st.image(img, caption="A black square", width=200)


if st.checkbox("Show image", True):
    image()


# Regression tests for PR #14565 / issue #14555:
# The cache spinner overlay must not visually hide or clip the first element
# rendered inside a @st.cache_data function — regardless of which element
# happens to be first (progress, text, markdown, image, ...).

if "cache_overlap_token" not in st.session_state:
    st.session_state.cache_overlap_token = 0


def _next_overlap_token() -> int:
    st.session_state.cache_overlap_token += 1
    return cast("int", st.session_state.cache_overlap_token)


@st.cache_data
def _cache_overlap_progress(token: int) -> int:
    # Use a static progress state so the snapshot is stable while the
    # cache spinner overlay is visible. The original bug surfaces from
    # the progress text overlapping the spinner text — that overlap is
    # already exercised by this static layout.
    st.progress(0.42, text="(42/100) Computing...")
    time.sleep(2)
    return token


@st.cache_data
def _cache_overlap_text(token: int) -> int:
    st.text("hello")
    time.sleep(2)
    return token


@st.cache_data
def _cache_overlap_markdown(token: int) -> int:
    # Descenders (p/g/j/y) exercise the gradient-clip case from the PR thread.
    st.markdown("# Heading pgjy")
    time.sleep(2)
    return token


@st.cache_data
def _cache_overlap_image(token: int) -> int:
    img: npt.NDArray[np.uint8] = np.tile(
        np.linspace(0, 255, 200, dtype=np.uint8), (80, 1)
    )
    st.image(img, caption="cache overlap image", clamp=True)
    time.sleep(2)
    return token


if st.button("Run cache spinner over progress"):
    with st.container(key="cache_overlap_progress_container"):
        _cache_overlap_progress(_next_overlap_token())

if st.button("Run cache spinner over text"):
    with st.container(key="cache_overlap_text_container"):
        _cache_overlap_text(_next_overlap_token())

if st.button("Run cache spinner over markdown"):
    with st.container(key="cache_overlap_markdown_container"):
        _cache_overlap_markdown(_next_overlap_token())

if st.button("Run cache spinner over image"):
    with st.container(key="cache_overlap_image_container"):
        _cache_overlap_image(_next_overlap_token())
