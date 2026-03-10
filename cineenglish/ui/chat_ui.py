from __future__ import annotations

import streamlit as st

from cineenglish.memory.user_profile import UserProfile
from cineenglish.ui.coach_chat_tab import render_coach_chat_tab
from cineenglish.ui.recommendations_tab import render_recommendations_tab
from cineenglish.ui.vocab_quiz_tab import render_vocab_quiz_tab
from cineenglish.ui.word_library_tab import render_word_library_tab


def _init_session_state() -> None:
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("profile", UserProfile())
    st.session_state.setdefault("vocab_quiz", None)
    st.session_state.setdefault("coach_messages", [])


def render_chat() -> None:
    _init_session_state()

    st.title("🎬 CineEnglish")
    st.caption(
        "Learn English through movies and series — genre-aware recommendations, vocab mining, and weekly progress."
    )

    tab_reco, tab_vocab, tab_library, tab_coach = st.tabs(
        ["Recommendations", "Vocab & Quiz", "Word Library", "Coach Chat"]
    )

    with tab_reco:
        render_recommendations_tab()
    with tab_vocab:
        render_vocab_quiz_tab()
    with tab_library:
        render_word_library_tab()
    with tab_coach:
        render_coach_chat_tab()

