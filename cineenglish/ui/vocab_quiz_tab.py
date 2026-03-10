from __future__ import annotations

import io
import urllib.parse as urlparse

import streamlit as st

from config import settings
from cineenglish.database.sqlite_db import SqliteDB


def _extract_youtube_id(raw: str) -> str:
    raw = raw.strip()
    if "v=" in raw or "youtube.com" in raw:
        parsed = urlparse.urlparse(raw)
        params = urlparse.parse_qs(parsed.query)
        return params.get("v", [raw])[0]
    if "youtu.be/" in raw:
        return raw.rsplit("/", 1)[-1]
    return raw


def render_vocab_quiz_tab() -> None:
    db: SqliteDB = st.session_state.db
    subtitle_agent = st.session_state.subtitle
    teaching_agent = st.session_state.teaching
    user_id: str = st.session_state.user_id

    st.write("### Choose your content source:")
    tab_yt, tab_file = st.tabs(["▶️ YouTube", "📁 Local File"])

    yt_video_id = ""
    yt_title = ""
    yt_level = settings.DEFAULT_LEVEL
    file_path = ""
    file_title = ""
    file_level = settings.DEFAULT_LEVEL
    upload_bytes = None

    with tab_yt:
        yt_raw = st.text_input("Paste YouTube video ID or full URL")
        yt_video_id = _extract_youtube_id(yt_raw) if yt_raw else ""
        yt_title = st.text_input("Title for this content (e.g. Suits S01E01)")
        yt_level = st.selectbox(
            "Your level",
            options=settings.CEFR_LEVELS,
            index=settings.CEFR_LEVELS.index(settings.DEFAULT_LEVEL),
            key="yt_level",
        )

    with tab_file:
        uploaded = st.file_uploader(
            "Upload video/subtitle file", type=["mp4", "mkv", "srt", "avi"]
        )
        file_title = st.text_input("Title for this content", key="file_title")
        file_level = st.selectbox(
            "Your level",
            options=settings.CEFR_LEVELS,
            index=settings.CEFR_LEVELS.index(settings.DEFAULT_LEVEL),
            key="file_level",
        )
        if uploaded is not None:
            upload_bytes = uploaded.read()
            tmp_path = f"/tmp/{uploaded.name}"
            with open(tmp_path, "wb") as f:
                f.write(upload_bytes)
            file_path = tmp_path

    st.write("")
    if st.button("🔍 Extract Vocab & Build Quiz", use_container_width=True):
        source = None
        level = settings.DEFAULT_LEVEL
        source_title = ""
        try:
            if yt_video_id and yt_title:
                source = "youtube"
                level = yt_level
                source_title = yt_title
            elif file_path and file_title:
                source = "file"
                level = file_level
                source_title = file_title

            if not source:
                st.error("Please provide either a YouTube link+title or upload a file + title.")
            else:
                progress = st.progress(0, text="Starting...")
                try:
                    progress.progress(25, text="🔍 Fetching subtitles...")
                    if source == "youtube":
                        vocab_items = subtitle_agent.process_youtube(
                            yt_video_id,
                            source_title=source_title,
                            level=level,
                            user_id=user_id,
                        )
                    else:
                        vocab_items = subtitle_agent.process_file(
                            file_path,
                            source_title=source_title,
                            level=level,
                            user_id=user_id,
                        )

                    progress.progress(50, text="📝 Extracting vocabulary...")
                    # word logging already happens inside subtitle_agent

                    progress.progress(75, text="📖 Looking up definitions...")
                    # definitions are prepared inside subtitle_agent as well

                    progress.progress(100, text="🧠 Building your quiz...")
                    quiz_questions = teaching_agent.build_quiz(vocab_items, level=level)
                finally:
                    progress.empty()

                st.session_state.current_vocab = vocab_items
                st.session_state.current_quiz = quiz_questions
                st.session_state.quiz_source = source_title
                st.session_state.quiz_answers = {}
                st.session_state.quiz_submitted = False
        except ValueError as e:
            st.error(f"❌ {str(e)}")
            st.stop()
        except Exception as e:  # pragma: no cover
            st.error(f"❌ Something went wrong: {str(e)}")
            st.stop()

    # Section 3 — Vocabulary Preview
    vocab_items = st.session_state.get("current_vocab")
    if vocab_items:
        st.write("### 📝 Words extracted:")
        rows = [
            {
                "Word": v.word,
                "Part of Speech": v.part_of_speech,
                "Definition": v.definition,
                "Scene Context": v.scene_context,
            }
            for v in vocab_items
        ]
        st.dataframe(rows, use_container_width=True)
        st.caption(f"Found {len(rows)} interesting words for your level.")

    # Section 4 — Quiz
    questions = st.session_state.get("current_quiz") or []
    if questions and not st.session_state.get("quiz_submitted", False):
        st.write("### 🧠 Quiz Time!")
        st.info(f"{len(questions)} questions based on what you just watched")

        for idx, q in enumerate(questions):
            st.write(f"**Q{idx + 1}: {q.question}**")
            answer = st.radio(
                "",
                options=q.options,
                key=f"quiz_q_{idx}",
                index=None,
            )
            if "quiz_answers" not in st.session_state:
                st.session_state.quiz_answers = {}
            st.session_state.quiz_answers[idx] = answer

        if st.button("✅ Check My Answers", use_container_width=True):
            answers = st.session_state.quiz_answers
            correct = 0
            for idx, q in enumerate(questions):
                user_ans = answers.get(idx)
                if user_ans is None:
                    continue
                # correct is letter A-D; map to option
                correct_idx = {"A": 0, "B": 1, "C": 2, "D": 3}.get(q.correct, 0)
                if correct_idx < len(q.options) and q.options[correct_idx] == user_ans:
                    correct += 1

            total = len(questions)
            score_pct = (correct / total) * 100 if total else 0
            st.session_state.quiz_submitted = True

            db.log_quiz_result(
                user_id=user_id,
                source_title=st.session_state.get("quiz_source", ""),
                total=total,
                correct=correct,
                level=st.session_state.user_level,
            )

            # Section 5 — Results summary
            if score_pct >= 80:
                st.success(
                    f"🎉 Excellent! {correct}/{total} correct ({score_pct:.0f}%)"
                )
            elif score_pct >= 60:
                st.warning(
                    f"👍 Good job! {correct}/{total} correct ({score_pct:.0f}%)"
                )
            else:
                st.error(
                    f"📚 Keep practicing! {correct}/{total} correct ({score_pct:.0f}%)"
                )

            for idx, q in enumerate(questions):
                user_ans = st.session_state.quiz_answers.get(idx)
                correct_idx = {"A": 0, "B": 1, "C": 2, "D": 3}.get(q.correct, 0)
                correct_text = (
                    q.options[correct_idx] if correct_idx < len(q.options) else ""
                )
                st.write(f"**Q{idx + 1}: {q.question}**")
                if user_ans == correct_text:
                    st.write("✅ You answered correctly.")
                else:
                    st.write("❌ Your answer was incorrect.")
                    st.write(f"Correct answer: **{correct_text}**")
                if q.explanation:
                    st.caption(q.explanation)

            if st.button("🔄 Try Another Video", use_container_width=True):
                for key in [
                    "current_vocab",
                    "current_quiz",
                    "quiz_source",
                    "quiz_answers",
                    "quiz_submitted",
                ]:
                    st.session_state.pop(key, None)


