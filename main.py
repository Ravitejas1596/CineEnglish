from __future__ import annotations

import os

import streamlit as st
from groq import Groq

from config import (
    APP_ICON,
    APP_TITLE,
    CHROMA_DB_PATH,
    DAILY_EMAIL_HOUR,
    DEFAULT_LEVEL,
    DEFAULT_USER_ID,
    GMAIL_CREDENTIALS_FILE,
    GMAIL_SCOPES,
    GMAIL_SENDER,
    GMAIL_TOKEN_FILE,
    GROQ_API_KEY,
    SQLITE_DB_PATH,
    TMDB_API_KEY,
    EMBEDDING_MODEL,
    REPORTS_DIR,
)
from cineenglish.database.sqlite_db import SqliteDB
from cineenglish.memory.chroma_store import ChromaStore
from cineenglish.memory.conversation_memory import ConversationMemory
from cineenglish.agents.maestro_agent import MaestroAgent
from cineenglish.agents.recommender_agent import RecommenderAgent
from cineenglish.agents.subtitle_agent import SubtitleAgent
from cineenglish.agents.teaching_agent import TeachingAgent
from cineenglish.agents.notification_agent import NotificationAgent
from cineenglish.agents.dictionary_agent import DictionaryAgent
from cineenglish.tools.tmdb_tool import TMDBTool
from cineenglish.tools.gmail_tool import GmailTool
from cineenglish.tools.report_tool import ReportTool
from cineenglish.ui.recommendations_tab import render_recommendations_tab
from cineenglish.ui.vocab_quiz_tab import render_vocab_quiz_tab
from cineenglish.ui.word_library_tab import render_word_library_tab
from cineenglish.ui.coach_chat_tab import render_coach_chat_tab


st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
/* Dark cinema theme */
.stApp {
    background-color: #0f0f0f;
    color: #ffffff;
}

/* Force ALL text to be white/light */
.stApp p, .stApp span, .stApp div, .stApp label,
.stApp h1, .stApp h2, .stApp h3, .stApp h4 {
    color: #ffffff !important;
}

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: #1a1a1a;
    padding: 8px;
    border-radius: 12px;
}
.stTabs [data-baseweb="tab"] {
    background-color: #2a2a2a;
    color: #cccccc !important;
    border-radius: 8px;
    padding: 8px 20px;
    font-weight: 600;
}
.stTabs [aria-selected="true"] {
    background-color: #e50914 !important;
    color: white !important;
}

/* Buttons */
.stButton > button {
    background-color: #e50914;
    color: white !important;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    padding: 8px 20px;
    transition: opacity 0.2s;
    width: 100%;
}
.stButton > button:hover {
    opacity: 0.85;
    background-color: #e50914 !important;
    color: white !important;
}

/* Metric cards */
[data-testid="metric-container"] {
    background-color: #1a1a1a;
    border: 1px solid #333333;
    border-radius: 10px;
    padding: 16px;
}
[data-testid="metric-container"] label,
[data-testid="metric-container"] div {
    color: #ffffff !important;
}

/* Chat messages */
[data-testid="stChatMessage"] {
    background-color: #1a1a1a;
    border-radius: 10px;
    margin-bottom: 8px;
    padding: 12px;
}

/* Input fields — fix black text on black bg */
.stTextInput > div > div > input {
    background-color: #1a1a1a !important;
    color: #ffffff !important;
    border: 1px solid #333333 !important;
    border-radius: 8px;
}
.stTextInput > label {
    color: #cccccc !important;
}

/* Selectbox */
.stSelectbox > div > div {
    background-color: #1a1a1a !important;
    color: #ffffff !important;
    border: 1px solid #333333 !important;
}
.stSelectbox label {
    color: #cccccc !important;
}

/* Radio buttons */
.stRadio > label {
    color: #ffffff !important;
}
.stRadio > div > label {
    color: #ffffff !important;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    border: 1px solid #333333;
    border-radius: 8px;
}

/* File uploader */
.stFileUploader > div {
    background-color: #1a1a1a !important;
    border: 1px dashed #333333 !important;
    color: #ffffff !important;
}
.stFileUploader label {
    color: #cccccc !important;
}

/* Toggle */
.stToggle > label {
    color: #ffffff !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #1a1a1a !important;
}
[data-testid="stSidebar"] * {
    color: #ffffff !important;
}

/* Progress bar */
.stProgress > div > div {
    background-color: #e50914 !important;
}

/* Caption text */
.stMarkdown small, .stCaption {
    color: #aaaaaa !important;
}

/* Divider */
hr {
    border-color: #333333 !important;
}

/* Success/warning/error/info */
.stSuccess { background-color: #1a3a1a !important; color: #ffffff !important; }
.stWarning { background-color: #3a2a00 !important; color: #ffffff !important; }
.stError   { background-color: #3a1a1a !important; color: #ffffff !important; }
.stInfo    { background-color: #1a2a3a !important; color: #ffffff !important; }

/* Hide streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""",
    unsafe_allow_html=True,
)


def check_env() -> None:
    missing: list[str] = []
    if not GROQ_API_KEY:
        missing.append("GROQ_API_KEY")
    if not TMDB_API_KEY:
        missing.append("TMDB_API_KEY")
    if missing:
        st.warning(
            "⚠️ Missing API keys in environment: "
            + ", ".join(missing)
            + "\n\nSet them either in a local .env file (for local runs) or in "
            "Streamlit Cloud Secrets (for deployed app). Some features that rely "
            "on these APIs may be limited."
        )


@st.cache_resource
def initialize_app() -> dict:
    """
    Initialize all components once and cache them.
    """
    # 1. SQLite DB
    db = SqliteDB(SQLITE_DB_PATH)
    db.ensure_user(DEFAULT_USER_ID, DEFAULT_LEVEL)

    # 2. Groq client (best-effort only; may be unavailable on some platforms)
    try:
        groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
    except TypeError:
        # Some hosted environments bundle an incompatible httpx version,
        # causing Groq's internal HTTP client to fail on construction.
        # In that case we disable LLM features and rely on local fallbacks.
        groq_client = None

    # 3. ChromaDB (semantic memory) – best-effort only
    try:
        chroma = ChromaStore(path=CHROMA_DB_PATH, embedding_model=EMBEDDING_MODEL)
    except Exception:
        chroma = None

    # 4. Tools
    tmdb_tool = TMDBTool(api_key=TMDB_API_KEY)
    gmail_tool = GmailTool(
        credentials_file=GMAIL_CREDENTIALS_FILE,
        token_file=GMAIL_TOKEN_FILE,
        sender=GMAIL_SENDER,
        scopes=GMAIL_SCOPES,
    )
    report_tool = ReportTool(reports_dir=REPORTS_DIR)

    # 5. Agents
    dictionary_agent = DictionaryAgent()
    subtitle_agent = SubtitleAgent(db=db)
    teaching_agent = TeachingAgent(groq_client=groq_client)
    recommender_agent = RecommenderAgent(tmdb_api_key=TMDB_API_KEY)
    notification_agent = NotificationAgent(
        db=db,
        gmail_tool=gmail_tool,
        report_tool=report_tool,
    )

    return {
        "db": db,
        "groq_client": groq_client,
        "chroma": chroma,
        "tmdb_tool": tmdb_tool,
        "gmail_tool": gmail_tool,
        "report_tool": report_tool,
        "dictionary_agent": dictionary_agent,
        "subtitle_agent": subtitle_agent,
        "teaching_agent": teaching_agent,
        "recommender_agent": recommender_agent,
        "notification_agent": notification_agent,
    }


def setup_session_state(components: dict) -> None:
    """
    Load components into st.session_state once.
    """
    if "initialized" in st.session_state:
        return

    db = components["db"]
    groq_client = components["groq_client"]
    chroma = components["chroma"]

    # Conversation memory (per session)
    memory = ConversationMemory(chroma_store=chroma, user_id=DEFAULT_USER_ID)

    # Maestro agent
    maestro = MaestroAgent(db=db, memory=memory, groq_client=groq_client)

    st.session_state.db = db
    st.session_state.chroma = chroma
    st.session_state.memory = memory
    st.session_state.maestro = maestro
    st.session_state.recommender = components["recommender_agent"]
    st.session_state.subtitle = components["subtitle_agent"]
    st.session_state.teaching = components["teaching_agent"]
    st.session_state.notification = components["notification_agent"]
    st.session_state.gmail_tool = components["gmail_tool"]
    st.session_state.report_tool = components["report_tool"]
    st.session_state.user_id = DEFAULT_USER_ID
    st.session_state.user_level = DEFAULT_LEVEL

    # UI state defaults
    st.session_state.active_tab = "recommendations"
    st.session_state.chat_messages = []
    st.session_state.current_quiz = None
    st.session_state.current_vocab = None
    st.session_state.quiz_submitted = False
    st.session_state.quiz_answers = {}
    st.session_state.rec_results = []
    st.session_state.rec_media_type = "movie"
    st.session_state.rec_genre = None
    st.session_state.notify_daily = True
    st.session_state.notify_weekly = True
    st.session_state.user_email = ""

    st.session_state.initialized = True


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("# 🎬 CineEnglish")
        st.markdown("Learn English through movies & series")

        st.divider()

        # Level selector
        st.write("**Your Level:**")
        current_level = st.session_state.get("user_level", DEFAULT_LEVEL)
        levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
        level = st.selectbox(
            label="",
            options=levels,
            index=levels.index(current_level),
            key="level_selector",
            label_visibility="collapsed",
        )
        if level != st.session_state.user_level:
            st.session_state.user_level = level
            st.session_state.db.ensure_user(DEFAULT_USER_ID, level)

        st.divider()

        # Quick stats
        st.write("**Quick Stats:**")
        stats = st.session_state.db.progress_overview(DEFAULT_USER_ID)
        st.metric("Words Learned", stats.get("total_words", 0))
        st.metric("Current Streak", f"{stats.get('current_streak', 0)} days 🔥")
        st.metric("Avg Quiz Score", f"{(stats.get('avg_score') or 0):.0f}%")

        st.divider()

        # API status
        st.write("**System Status:**")
        groq_ok = bool(GROQ_API_KEY)
        tmdb_ok = bool(TMDB_API_KEY)
        gmail_ok = bool(GMAIL_SENDER)

        st.write(f'{"🟢" if groq_ok else "🔴"} Groq LLM')
        st.write(f'{"🟢" if tmdb_ok else "🔴"} TMDB Movies')
        st.write(f'{"🟢" if gmail_ok else "🔴"} Gmail Notifications')
        st.write("🟢 Dictionary API")
        st.write("🟢 YouTube Transcripts")

        st.divider()
        st.caption("CineEnglish v1.0 — $0 to run")


def render_header() -> None:
    db: SqliteDB = st.session_state.db
    user_id: str = st.session_state.user_id
    user_level: str = st.session_state.user_level
    stats = db.progress_overview(user_id)

    c1, c2 = st.columns([4, 1])
    with c1:
        st.markdown("# 🎬 CineEnglish")
        st.markdown("*Learn English through movies & series you actually enjoy*")
    with c2:
        st.markdown(f"**Level:** {user_level}")
        st.markdown(f"**🔥 {stats.get('current_streak', 0)} day streak**")


def main() -> None:
    # Ensure env and data directories
    check_env()
    os.makedirs("./data/chroma_db", exist_ok=True)
    os.makedirs("./data/reports", exist_ok=True)
    components = initialize_app()
    setup_session_state(components)

    render_sidebar()
    render_header()
    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "🎬 Recommendations",
            "📝 Vocab & Quiz",
            "📚 Word Library",
            "🎓 Coach Chat",
        ]
    )
    with tab1:
        render_recommendations_tab()
    with tab2:
        render_vocab_quiz_tab()
    with tab3:
        render_word_library_tab()
    with tab4:
        render_coach_chat_tab()


if __name__ == "__main__":
    main()

