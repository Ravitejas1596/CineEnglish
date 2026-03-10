from __future__ import annotations

from dataclasses import dataclass
from typing import List

from groq import Groq

from config import settings
from cineenglish.agents.recommender_agent import RecommenderAgent
from cineenglish.database.sqlite_db import SqliteDB
from cineenglish.memory.conversation_memory import ConversationMemory


@dataclass(frozen=True)
class ConversationState:
    content_type: str | None = None  # "movie" or "series"
    genre: str | None = None
    intensity: str | None = None
    challenge: str | None = None
    liked_title: str | None = None


class MaestroAgent:
    """
    High-level orchestrator for CineEnglish.
    - Routes chat messages to intents.
    - Provides progress summaries.
    - Delegates recommendations to RecommenderAgent.
    """

    def __init__(
        self,
        db: SqliteDB,
        memory: ConversationMemory,
        groq_client: Groq | None = None,
    ) -> None:
        self.db = db
        self.memory = memory
        # Groq client is optional; when unavailable we fall back gracefully.
        self.client = groq_client
        self.model = settings.GROQ_MODEL
        self.recommender = RecommenderAgent()

    # Recommendation helper for UI (optional)
    def get_recommendations_for_state(
        self,
        state: ConversationState,
        level: str,
    ):
        if state.content_type is None or state.genre is None:
            return []
        mood_parts: List[str] = []
        if state.intensity:
            mood_parts.append(state.intensity)
        if state.challenge:
            mood_parts.append(state.challenge)
        mood = " / ".join(mood_parts)
        liked = state.liked_title or ""
        return self.recommender.get_recommendations(
            media_type=state.content_type,
            genre=state.genre,
            level=level,
            mood=mood,
            liked=liked,
        )

    # Intent classification ---------------------------------------------
    def classify_intent(self, message: str) -> str:
        t = message.lower()
        if any(k in t for k in ["how am i doing", "progress", "stats", "score", "streak", "report"]):
            return "progress"
        if any(k in t for k in ["quiz me", "test me", "practice", "question"]):
            return "quiz"
        if any(k in t for k in ["suggest", "recommend", "what should i watch", "what to watch"]):
            return "recommend"
        watched_keywords = [
            "watched",
            "finished",
            "just saw",
            "completed",
            "i saw",
            "i watched",
            "just watched",
            "i finished",
        ]
        if any(k in t for k in watched_keywords):
            return "watched"
        if any(k in t for k in ["word", "vocabulary", "meaning", "define", "what does"]):
            return "vocab"
        return "general"

    # Handlers ---------------------------------------------------------
    def handle_progress(self, user_id: str) -> str:
        stats = self.db.progress_overview(user_id)
        total_words = stats.get("total_words", 0)
        unique_words = stats.get("unique_words", 0)
        quizzes = stats.get("quizzes_taken", 0)
        avg_score = stats.get("avg_score") or 0.0
        streak = stats.get("current_streak", 0)
        score_text = f"{avg_score:.1f}%" if isinstance(avg_score, float) else "n/a"

        if total_words == 0 and quizzes == 0:
            return (
                "Here's how you're doing! 📊\n"
                "You haven't logged any learning yet. "
                "Start with a short scene in the Vocab & Quiz tab, and I'll track your progress."
            )

        motivation = (
            "Fantastic work, keep the streak alive! 🔥"
            if streak >= 3
            else "Nice start — a little practice every day goes a long way. 🙂"
        )

        return (
            "Here's how you're doing! 📊\n"
            f"You've learned {total_words} words total ({unique_words} unique).\n"
            f"Quizzes taken: {quizzes} | Average score: {score_text}\n"
            f"Current streak: {streak} days 🔥\n"
            f"{motivation}"
        )

    def handle_general(self, message: str, user_id: str) -> str:
        system_prompt = (
            "You are CineEnglish Coach, a friendly English learning assistant.\n"
            "You help users learn English through movies and series.\n"
            "Keep responses short (2-4 sentences), encouraging, and practical.\n"
            "If asked about watching content, direct them to the Vocab & Quiz tab.\n"
            "If asked for recommendations, direct them to the Recommendations tab."
        )
        if self.client is None:
            return "I'm having trouble connecting right now. Try again in a moment! 🔄"

        msgs = self.memory.build_groq_messages(system_prompt, message)
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=msgs,
                max_tokens=settings.GROQ_MAX_TOKENS,
                temperature=0.5,
            )
            content = resp.choices[0].message.content or ""
        except Exception:
            content = "I'm having trouble connecting right now. Try again in a moment! 🔄"
        return content

    # Public chat API --------------------------------------------------
    def chat(self, user_id: str, message: str) -> str:
        self.memory.add_message("user", message)
        intent = self.classify_intent(message)

        if intent == "progress":
            response = self.handle_progress(user_id)
        elif intent == "quiz":
            response = (
                "Head to the Vocab & Quiz tab to start a quiz! 🎯 "
                "Pick a YouTube video or local file and I'll build a personalized quiz for your level."
            )
        elif intent == "recommend":
            response = (
                "Check out the Recommendations tab! 🎬 Pick your genre and mood and "
                "I'll suggest the perfect show for your level."
            )
        elif intent == "watched":
            response = (
                "Nice! Drop the YouTube link or file in the Vocab & Quiz tab and "
                "I'll extract vocabulary from it automatically. 📝"
            )
        else:  # vocab or general
            response = self.handle_general(message, user_id)

        self.memory.add_message("assistant", response)
        return response
