from __future__ import annotations

import streamlit as st

from cineenglish.database.sqlite_db import SqliteDB
from config import settings


def render_word_library_tab() -> None:
    db: SqliteDB = st.session_state.db
    teaching_agent = st.session_state.teaching
    memory = st.session_state.memory
    user_id: str = st.session_state.user_id
    user_level: str = st.session_state.user_level

    st.write("### 📚 Your Word Library")
    stats = db.progress_overview(user_id)
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Words", stats.get("total_words", 0))
    col2.metric("Unique Words", stats.get("unique_words", 0))
    col3.metric("Quizzes Taken", stats.get("quizzes_taken", 0))

    # Source selector
    sources = db.list_sources(user_id)
    if not sources:
        st.info("No words yet! Go to Vocab & Quiz tab to extract vocabulary.")
        return

    selected_source = st.selectbox(
        "📂 Browse by source:",
        options=sources,
        help="Each source is a movie, episode, or clip you've learned from",
    )

    # Strip "(N words)" suffix
    source_title = selected_source.rsplit("(", 1)[0].strip()
    words = db.words_for_source(user_id, source_title)
    st.write(f"**{len(words)} words** from *{source_title}*")

    table_rows = [
        {"Word": w["word"], "Scene Context": w.get("scene_context") or ""}
        for w in words
    ]
    st.dataframe(table_rows, use_container_width=True)

    st.write("---")
    c1, c2 = st.columns([2, 1])
    with c1:
        st.write("Want to practice these words again?")
    with c2:
        if st.button("🧠 Build Quiz from This Source", use_container_width=True):
            quiz = teaching_agent.rebuild_quiz_from_words(words, level=user_level)
            st.session_state.current_quiz = quiz
            st.session_state.quiz_source = source_title
            st.session_state.quiz_submitted = False
            st.session_state.quiz_answers = {}
            st.success("Quiz ready! Head to the Vocab & Quiz tab 🎯")
            if st.button("Go to Vocab & Quiz →"):
                st.session_state.active_tab = "vocab_quiz"

    # Search section
    st.write("---")
    st.write("### 🔍 Search your vocabulary")
    search_query = st.text_input("Search for a word...")
    if search_query:
        results = memory.chroma_store.search_vocabulary(
            user_id=user_id, query=search_query, n_results=5
        )
        if not results:
            st.info("No matching words found yet.")
        else:
            for r in results:
                with st.container(border=True):
                    st.markdown(f"**{r.get('word')}**")
                    st.markdown(r.get("definition", ""))
                    st.caption(
                        f"Source: {r.get('source_title','')} · Context: {r.get('scene_context','')}"
                    )


