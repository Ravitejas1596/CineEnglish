from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List

from dotenv import load_dotenv

# Load .env once at import time
load_dotenv()


@dataclass(frozen=True)
class Settings:
    # LLM (Groq)
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    GROQ_MAX_TOKENS: int = int(os.getenv("GROQ_MAX_TOKENS", "1024"))

    # TMDB
    TMDB_API_KEY: str = os.getenv("TMDB_API_KEY", "")
    TMDB_BASE_URL: str = "https://api.themoviedb.org/3"

    # Dictionary
    DICTIONARY_API_URL: str = "https://api.dictionaryapi.dev/api/v2/entries/en"

    # Gmail API (OAuth flow expected via credentials.json / token.json)
    GMAIL_CREDENTIALS_FILE: str = "credentials.json"
    GMAIL_TOKEN_FILE: str = "token.json"
    GMAIL_SENDER: str = os.getenv("GMAIL_SENDER", "")
    GMAIL_SCOPES: List[str] = field(
        default_factory=lambda: ["https://www.googleapis.com/auth/gmail.send"]
    )

    # Chroma / embeddings
    CHROMA_DB_PATH: str = "./data/chroma_db"
    CHROMA_COLLECTION_CONVERSATIONS: str = "user_conversations"
    CHROMA_COLLECTION_VOCABULARY: str = "vocabulary_bank"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # SQLite / reports
    SQLITE_DB_PATH: str = "./data/cineenglish.db"
    REPORTS_DIR: str = "./data/reports"

    # Users / levels
    DEFAULT_USER_ID: str = "default"
    CEFR_LEVELS: List[str] = field(
        default_factory=lambda: ["A1", "A2", "B1", "B2", "C1", "C2"]
    )
    DEFAULT_LEVEL: str = "B1"

    # Genres (TMDB IDs)
    SUPPORTED_GENRES: Dict[str, int] = field(
        default_factory=lambda: {
            "Drama": 18,
            "Comedy": 35,
            "Crime & Thriller": 80,
            "Sci-Fi": 878,
            "Action": 28,
        }
    )

    # Vocab settings
    MIN_WORD_LENGTH: int = 5
    MAX_VOCAB_PER_SESSION: int = 20
    STOP_WORDS: List[str] = field(
        default_factory=lambda: [
            "about",
            "after",
            "would",
            "could",
            "should",
            "their",
            "there",
            "where",
            "which",
            "while",
            "these",
            "those",
            "every",
            "other",
            "never",
            "always",
            "still",
            "going",
            "being",
            "having",
            "people",
            "think",
            "thing",
            "right",
            "gonna",
            "wanna",
            "yeah",
        ]
    )

    # Scheduler defaults
    DAILY_EMAIL_HOUR: int = 8
    WEEKLY_EMAIL_DAY: str = "mon"
    MONTHLY_EMAIL_DAY: int = 1


settings = Settings()

# Convenience module-level constants for main.py imports
GROQ_API_KEY = settings.GROQ_API_KEY
GROQ_MODEL = settings.GROQ_MODEL
GROQ_MAX_TOKENS = settings.GROQ_MAX_TOKENS

TMDB_API_KEY = settings.TMDB_API_KEY
TMDB_BASE_URL = settings.TMDB_BASE_URL

DICTIONARY_API_URL = settings.DICTIONARY_API_URL

GMAIL_CREDENTIALS_FILE = settings.GMAIL_CREDENTIALS_FILE
GMAIL_TOKEN_FILE = settings.GMAIL_TOKEN_FILE
GMAIL_SENDER = settings.GMAIL_SENDER
GMAIL_SCOPES = settings.GMAIL_SCOPES

CHROMA_DB_PATH = settings.CHROMA_DB_PATH
CHROMA_COLLECTION_CONVERSATIONS = settings.CHROMA_COLLECTION_CONVERSATIONS
CHROMA_COLLECTION_VOCABULARY = settings.CHROMA_COLLECTION_VOCABULARY
EMBEDDING_MODEL = settings.EMBEDDING_MODEL

SQLITE_DB_PATH = settings.SQLITE_DB_PATH
REPORTS_DIR = settings.REPORTS_DIR

DEFAULT_USER_ID = settings.DEFAULT_USER_ID
DEFAULT_LEVEL = settings.DEFAULT_LEVEL
CEFR_LEVELS = settings.CEFR_LEVELS
SUPPORTED_GENRES = settings.SUPPORTED_GENRES
MIN_WORD_LENGTH = settings.MIN_WORD_LENGTH
MAX_VOCAB_PER_SESSION = settings.MAX_VOCAB_PER_SESSION
STOP_WORDS = settings.STOP_WORDS

DAILY_EMAIL_HOUR = settings.DAILY_EMAIL_HOUR
WEEKLY_EMAIL_DAY = settings.WEEKLY_EMAIL_DAY
MONTHLY_EMAIL_DAY = settings.MONTHLY_EMAIL_DAY

# App metadata for UI
APP_TITLE = "CineEnglish"
APP_ICON = "🎬"

