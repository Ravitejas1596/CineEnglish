from __future__ import annotations

import io

import streamlit as st

from cineenglish.database.sqlite_db import SqliteDB
from cineenglish.tools.report_tool import ReportTool


def render_coach_chat_tab() -> None:
    db: SqliteDB = st.session_state.db
    maestro = st.session_state.maestro
    user_id: str = st.session_state.user_id
    user_level: str = st.session_state.user_level

    st.write("### 🎓 Your English Coach")
    st.caption("Ask me anything — your progress, what to watch, or practice English!")

    # Progress snapshot
    stats = db.progress_overview(user_id)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Words Learned", stats.get("total_words", 0))
    avg = stats.get("avg_score")
    col2.metric("Quiz Avg", f"{(avg or 0):.0f}%")
    col3.metric("Streak", f"{stats.get('current_streak', 0)}d 🔥")
    col4.metric("Level", user_level)
    st.divider()

    # Chat history
    st.session_state.setdefault("chat_messages", [])
    for m in st.session_state.chat_messages:
        with st.chat_message(m["role"]):
            st.write(m["content"])

    # Quick actions
    if not st.session_state.chat_messages:
        st.write("**Quick actions:**")
        c1, c2, c3, c4 = st.columns(4)
        quick_prompt = None
        with c1:
            if st.button("📊 How am I doing?"):
                quick_prompt = "How am I doing with my English progress?"
        with c2:
            if st.button("🎬 Suggest something to watch"):
                quick_prompt = "Can you suggest something to watch?"
        with c3:
            if st.button("🧠 Quiz me"):
                quick_prompt = "Quiz me on what I learned."
        with c4:
            if st.button("📝 What did I learn this week?"):
                quick_prompt = "What did I learn this week?"
        if quick_prompt:
            _handle_chat_turn(maestro, user_id, quick_prompt)
            st.rerun()

    # Chat input
    prompt = st.chat_input("Talk to your coach...")
    if prompt:
        _handle_chat_turn(maestro, user_id, prompt)
        st.rerun()

    # Email notifications + monthly report
    st.write("---")
    st.write("### 📧 Email Notifications")
    c1, c2 = st.columns(2)
    with c1:
        st.toggle(
            "Daily word digest",
            value=st.session_state.get("notify_daily", True),
            key="notify_daily",
        )
    with c2:
        st.toggle(
            "Weekly progress email",
            value=st.session_state.get("notify_weekly", True),
            key="notify_weekly",
        )

    email_input = st.text_input(
        "Your email for notifications:",
        value=st.session_state.get("user_email", ""),
        placeholder="you@gmail.com",
    )
    if email_input:
        st.session_state.user_email = email_input
        st.caption("✅ Notifications will be sent to this email")

    if st.button("📄 Generate Monthly Report Now"):
        today = st.session_state.get("today_override")  # optional for tests
        from datetime import date

        d = today or date.today()
        stats_month = db.monthly_stats(user_id, year=d.year, month=d.month)
        report_tool = ReportTool()
        pdf_path = report_tool.generate(
            user_id,
            {
                "month_name": d.strftime("%B"),
                "year": d.year,
                "level_start": stats.get("level", user_level),
                "level_end": stats.get("level", user_level),
                "words_learned": stats_month.get("words_learned", 0),
                "words_retained": stats_month.get("unique_words", 0),
                "retention_pct": 0,
                "quizzes_taken": stats_month.get("quizzes_taken", 0),
                "avg_score": stats_month.get("avg_score", 0),
                "hours_watched": 0.0,
                "top_sources": [],
                "weak_areas": [],
            },
            [],
        )
        if pdf_path:
            st.success("Report generated!")
            with open(pdf_path, "rb") as f:
                data = f.read()
            st.download_button(
                "⬇️ Download PDF",
                data=data,
                file_name="cineenglish_report.pdf",
                mime="application/pdf",
            )
        else:
            st.error("Could not generate PDF report in this environment.")


def _handle_chat_turn(maestro, user_id: str, prompt: str) -> None:
    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Coach is thinking..."):
            response = maestro.chat(user_id, prompt)
        st.write(response)
    st.session_state.chat_messages.append({"role": "assistant", "content": response})


