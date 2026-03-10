from __future__ import annotations

from dataclasses import dataclass

import streamlit as st


@dataclass(frozen=True)
class RecommendationCard:
    title: str
    content_type_label: str  # "Movie" / "Series"
    rating: float | None
    genre: str
    cefr_band: str
    why: str


def render_recommendation_card(card: RecommendationCard, *, key_prefix: str = "cineenglish"):
    rating = f"{card.rating:.1f}" if card.rating is not None else "—"
    st.markdown(
        f"""
<div style="
  border: 1px solid rgba(255,255,255,0.15);
  border-radius: 14px;
  padding: 16px 16px;
  background: rgba(255,255,255,0.02);
">
  <div style="font-size: 18px; font-weight: 700; margin-bottom: 6px;">
    🎬 {card.title} <span style="font-weight: 500; opacity: 0.85;">({card.content_type_label})</span>
  </div>
  <div style="opacity: 0.9; margin-bottom: 10px;">
    ⭐ <b>{rating}</b> &nbsp;|&nbsp; {card.genre}
  </div>
  <div style="margin-bottom: 10px;">
    📈 <b>Great for:</b> {card.cefr_band} learners
  </div>
  <div style="opacity: 0.95; margin-bottom: 12px;">
    🗣️ <b>Why:</b> {card.why}
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        start = st.button("▶ Start Learning", use_container_width=True, key=f"{key_prefix}-start")
    with c2:
        save = st.button("Save List", use_container_width=True, key=f"{key_prefix}-save")
    return {"start_learning": start, "save_list": save}
