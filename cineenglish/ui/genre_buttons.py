from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import streamlit as st


ContentType = Literal["movie", "series"]
Genre = Literal["Drama", "Comedy", "Crime & Thriller", "Sci-Fi", "Action"]


@dataclass(frozen=True)
class Selection:
    content_type: ContentType
    genre: Genre


def render_type_buttons(*, key_prefix: str = "cineenglish") -> ContentType | None:
    cols = st.columns(2)
    with cols[0]:
        if st.button("🎬 Movies", use_container_width=True, key=f"{key_prefix}-type-m"):
            return "movie"
    with cols[1]:
        if st.button("📺 Series", use_container_width=True, key=f"{key_prefix}-type-s"):
            return "series"
    return None


def render_genre_buttons(*, key_prefix: str = "cineenglish") -> Genre | None:
    row1 = st.columns(3)
    row2 = st.columns(2)

    with row1[0]:
        if st.button("Drama", use_container_width=True, key=f"{key_prefix}-g-drama"):
            return "Drama"
    with row1[1]:
        if st.button("Comedy", use_container_width=True, key=f"{key_prefix}-g-comedy"):
            return "Comedy"
    with row1[2]:
        if st.button(
            "Crime & Thriller", use_container_width=True, key=f"{key_prefix}-g-crime"
        ):
            return "Crime & Thriller"

    with row2[0]:
        if st.button("Sci-Fi", use_container_width=True, key=f"{key_prefix}-g-scifi"):
            return "Sci-Fi"
    with row2[1]:
        if st.button("Action", use_container_width=True, key=f"{key_prefix}-g-action"):
            return "Action"

    return None
