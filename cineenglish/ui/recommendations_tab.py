from __future__ import annotations

import streamlit as st

from config import settings
from cineenglish.database.sqlite_db import SqliteDB
from cineenglish.agents.recommender_agent import RecommendationCard


def _on_watch_clicked(
    card: RecommendationCard,
    user_id: str,
    db: SqliteDB,
    subtitle_agent,
    teaching_agent,
) -> None:
    # Step 1 — Log to watch history
    db.log_watch(
        user_id=user_id,
        title=card.title,
        media_type=card.media_type,
        genre=card.genre,
        episode="",
    )

    # Step 2/3 — Try to get a YouTube transcript for this title
    search_query = f"{card.title} english scene"
    try:
        from youtubesearchpython import VideosSearch

        results = VideosSearch(search_query, limit=5).result()
        video_ids = [r["id"] for r in results.get("result", [])]

        vocab_items = None
        for vid_id in video_ids:
            try:
                vocab_items = subtitle_agent.process_youtube(
                    video_id=vid_id,
                    source_title=card.title,
                    level=st.session_state.user_level,
                    user_id=user_id,
                )
                if vocab_items:
                    break
            except Exception:
                continue

        if vocab_items:
            # Step 4 — Log words to DB (already logged in subtitle_agent; this is extra safety)
            words_to_log = [
                {
                    "word": v.word,
                    "definition": v.definition,
                    "scene_context": v.scene_context,
                    "source_title": card.title,
                    "source_type": "youtube",
                }
                for v in vocab_items
            ]
            db.log_words(user_id, words_to_log)

            # Step 5 — Build quiz and store in session
            quiz = teaching_agent.build_quiz(vocab_items, st.session_state.user_level)
            st.session_state.current_vocab = vocab_items
            st.session_state.current_quiz = quiz
            st.session_state.quiz_source = card.title
            st.session_state.quiz_submitted = False
            st.session_state.quiz_answers = {}

            st.success(
                f"✅ Logged to watch history! Found {len(vocab_items)} words from '{card.title}'. "
                "Head to Vocab & Quiz tab to take your quiz! 🎯"
            )
        else:
            st.success(
                f"✅ '{card.title}' added to your watch list! "
                "Go to Vocab & Quiz tab and paste a YouTube clip from this show to extract vocabulary."
            )

    except ImportError:
        st.success(
            f"✅ '{card.title}' logged! Go to Vocab & Quiz tab, paste a YouTube clip from this show, "
            "and I'll extract vocabulary for you."
        )
    except Exception:
        st.warning(
            "✅ Logged to watch history! To get vocabulary, paste a clip in the Vocab & Quiz tab."
        )


def render_recommendations_tab() -> None:
    db: SqliteDB = st.session_state.db
    recommender = st.session_state.recommender
    subtitle_agent = st.session_state.subtitle
    teaching_agent = st.session_state.teaching
    user_id: str = st.session_state.user_id
    user_level: str = st.session_state.user_level

    st.session_state.setdefault("rec_media_type", "movie")
    st.session_state.setdefault("rec_genre", "Drama")
    st.session_state.setdefault("rec_mood_intensity", "")
    st.session_state.setdefault("rec_mood_difficulty", "")
    st.session_state.setdefault("rec_liked_show", "")
    st.session_state.setdefault("rec_results", [])

    media_type = st.session_state.rec_media_type
    genre = st.session_state.rec_genre

    # Step 1 — Type selector
    st.write("### What are you in the mood for?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎬 Movies", use_container_width=True):
            st.session_state.rec_media_type = "movie"
            media_type = "movie"
    with col2:
        if st.button("📺 Series", use_container_width=True):
            st.session_state.rec_media_type = "series"
            media_type = "series"

    # Step 2 — Genre selector
    st.write("### Pick a genre:")
    genres = ["Drama", "Comedy", "Crime & Thriller", "Sci-Fi", "Action"]
    cols = st.columns(len(genres))
    for i, g in enumerate(genres):
        with cols[i]:
            is_selected = genre == g
            if st.button(
                g,
                use_container_width=True,
                type="primary" if is_selected else "secondary",
                key=f"rec_genre_{g}",
            ):
                st.session_state.rec_genre = g
                genre = g

    # Step 3 — Mood refinement
    if genre:
        st.write("### Tell me more (optional):")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("😤 Intense", key="mood_intense"):
                st.session_state.rec_mood_intensity = "intense"
            if st.button("😌 Light", key="mood_light"):
                st.session_state.rec_mood_intensity = "light"
        with c2:
            if st.button("🧠 Challenge me", key="mood_challenge"):
                st.session_state.rec_mood_difficulty = "challenge"
            if st.button("😊 Comfort watch", key="mood_comfort"):
                st.session_state.rec_mood_difficulty = "comfort"

        liked_show = st.text_input(
            "Loved a specific show? (e.g. Suits, Breaking Bad)",
            value=st.session_state.rec_liked_show,
        )
        st.session_state.rec_liked_show = liked_show.strip()

    # Step 4 — Get Recommendations
    if genre:
        if st.button("🔎 Get Recommendations", type="primary", use_container_width=True):
            mood = " / ".join(
                m
                for m in [
                    st.session_state.rec_mood_intensity,
                    st.session_state.rec_mood_difficulty,
                ]
                if m
            )
            with st.spinner("Finding perfect content for your level..."):
                recs = recommender.get_recommendations(
                    media_type=media_type,
                    genre=genre,
                    level=user_level,
                    mood=mood,
                    liked=st.session_state.rec_liked_show,
                )
            st.session_state.rec_results = recs

    # Step 5 — Recommendation cards
    results: list[RecommendationCard] = st.session_state.rec_results
    if results:
        st.write("### 🎬 Suggestions for you")
        for card in results:
            with st.container():
                st.markdown(
                    """
                    <div style="
                        background-color: #1a1a1a;
                        border: 1px solid #333333;
                        border-radius: 12px;
                        padding: 20px;
                        margin-bottom: 16px;
                    ">
                    """,
                    unsafe_allow_html=True,
                )
                left, right = st.columns([1, 3])
                with left:
                    if card.poster_url:
                        st.image(card.poster_url, use_column_width=True)
                    else:
                        st.markdown(
                            """
                            <div style="
                                background-color: #2a2a2a;
                                height: 200px;
                                border-radius: 8px;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                font-size: 48px;
                            ">🎬</div>
                            """,
                            unsafe_allow_html=True,
                        )
                with right:
                    st.markdown(f"### {card.title}")
                    st.markdown(f"⭐ **{card.rating:.1f}/10**")
                    st.markdown(
                        f"**Genre:** {card.genre} &nbsp;&nbsp; **Type:** {card.media_type.title()}"
                    )
                    st.markdown(f"**Best for:** {card.cefr_band} learners")
                    st.markdown(f"📚 *{card.why_good_for_learning}*")
                    overview = card.overview or ""
                    st.markdown(
                        overview[:200] + ("..." if len(overview) > 200 else "")
                    )

                    if st.button(
                        "✅ I'll watch this",
                        key=f"watch_{card.tmdb_id}",
                        use_container_width=True,
                    ):
                        _on_watch_clicked(
                            card,
                            user_id=user_id,
                            db=db,
                            subtitle_agent=subtitle_agent,
                            teaching_agent=teaching_agent,
                        )
                st.markdown("</div>", unsafe_allow_html=True)


