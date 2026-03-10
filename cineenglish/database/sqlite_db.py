from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

from config import settings


class SqliteDB:
    def __init__(self, db_path: str | None = None) -> None:
        self.path = Path(db_path or settings.SQLITE_DB_PATH)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.init_schema()
        self.ensure_user(settings.DEFAULT_USER_ID, settings.DEFAULT_LEVEL)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.path))
        conn.row_factory = sqlite3.Row
        return conn

    def init_schema(self) -> None:
        schema_path = Path(__file__).with_name("schema.sql")
        with self.connect() as conn:
            with schema_path.open("r", encoding="utf-8") as f:
                conn.executescript(f.read())
            conn.commit()

    def ensure_user(self, user_id: str, level: str) -> None:
        now = datetime.utcnow().isoformat()
        with self.connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO users (id, created_at, level, streak_days, last_active) "
                "VALUES (?, ?, ?, 0, ?)",
                (user_id, now, level, now),
            )
            conn.commit()

    def log_words(self, user_id: str, words: List[Dict[str, Any]]) -> None:
        """
        words: list of dicts with keys:
          - word
          - definition
          - scene_context
          - source_title
          - source_type
        """
        if not words:
            return
        now = datetime.utcnow().isoformat()
        with self.connect() as conn:
            conn.executemany(
                "INSERT INTO word_logs (user_id, word, definition, scene_context, "
                "source_title, source_type, logged_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        user_id,
                        w.get("word"),
                        w.get("definition"),
                        w.get("scene_context"),
                        w.get("source_title"),
                        w.get("source_type"),
                        now,
                    )
                    for w in words
                ],
            )
            conn.commit()

    def log_quiz_result(
        self, user_id: str, source_title: str, total: int, correct: int, level: str
    ) -> None:
        score_pct = (correct / total) * 100 if total > 0 else 0.0
        now = datetime.utcnow().isoformat()
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO quiz_results (user_id, source_title, total_questions, "
                "correct_answers, score_pct, level, taken_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (user_id, source_title, total, correct, score_pct, level, now),
            )
            conn.commit()

    def log_watch(
        self,
        user_id: str,
        title: str,
        media_type: str,
        genre: str,
        episode: str | None = None,
        notes: str | None = None,
    ) -> None:
        now = datetime.utcnow().isoformat()
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO watch_history (user_id, title, media_type, genre, episode, watched_at, notes) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (user_id, title, media_type, genre, episode, now, notes),
            )
            conn.commit()

    def progress_overview(self, user_id: str) -> Dict[str, Any]:
        """
        Return a safe overview dict; never raise on failure.
        """
        defaults: Dict[str, Any] = {
            "total_words": 0,
            "unique_words": 0,
            "quizzes_taken": 0,
            "avg_score": 0.0,
            "current_streak": 0,
            "last_active": "Never",
            "level": settings.DEFAULT_LEVEL,
        }
        try:
            with self.connect() as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT COUNT(*) as total_words, COUNT(DISTINCT word) as unique_words "
                    "FROM word_logs WHERE user_id = ?",
                    (user_id,),
                )
                words_row = cur.fetchone() or {}

                cur.execute(
                    "SELECT COUNT(*) as quizzes_taken, AVG(score_pct) as avg_score "
                    "FROM quiz_results WHERE user_id = ?",
                    (user_id,),
                )
                quiz_row = cur.fetchone() or {}

                cur.execute(
                    "SELECT streak_days, last_active, level FROM users WHERE id = ?",
                    (user_id,),
                )
                user_row = cur.fetchone() or {}

            total_words = int(words_row.get("total_words") or 0)
            unique_words = int(words_row.get("unique_words") or 0)
            quizzes_taken = int(quiz_row.get("quizzes_taken") or 0)
            avg_score_raw = quiz_row.get("avg_score")
            avg_score = float(avg_score_raw) if avg_score_raw is not None else 0.0
            current_streak = int(user_row.get("streak_days") or 0)
            last_active = user_row.get("last_active") or "Never"
            level = user_row.get("level") or settings.DEFAULT_LEVEL

            return {
                "total_words": total_words,
                "unique_words": unique_words,
                "quizzes_taken": quizzes_taken,
                "avg_score": avg_score,
                "current_streak": current_streak,
                "last_active": last_active,
                "level": level,
            }
        except Exception:
            return defaults

    def list_sources(self, user_id: str) -> List[str]:
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT source_title, COUNT(*) as cnt "
                "FROM word_logs WHERE user_id = ? "
                "GROUP BY source_title ORDER BY MAX(logged_at) DESC",
                (user_id,),
            )
            rows = cur.fetchall()
        out: List[str] = []
        for r in rows:
            title = r["source_title"] or "Unknown source"
            cnt = int(r["cnt"] or 0)
            out.append(f"{title} ({cnt} words)")
        return out

    def words_for_source(self, user_id: str, source_title: str) -> List[Dict[str, Any]]:
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT word, scene_context FROM word_logs "
                "WHERE user_id = ? AND source_title = ? "
                "ORDER BY logged_at DESC",
                (user_id, source_title),
            )
            rows = cur.fetchall()
        return [{"word": r["word"], "scene_context": r["scene_context"]} for r in rows]

    def recent_words(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT word, scene_context, source_title, logged_at "
                "FROM word_logs WHERE user_id = ? "
                "ORDER BY logged_at DESC LIMIT ?",
                (user_id, limit),
            )
            rows = cur.fetchall()
        return [
            {
                "word": r["word"],
                "scene_context": r["scene_context"],
                "source_title": r["source_title"],
                "logged_at": r["logged_at"],
            }
            for r in rows
        ]

    def monthly_stats(self, user_id: str, year: int, month: int) -> Dict[str, Any]:
        """
        Aggregate stats for report generation.
        Always returns a complete dict with safe defaults.
        """
        from calendar import month_name
        from dateutil.relativedelta import relativedelta

        start = datetime(year, month, 1)
        end = start + relativedelta(months=1)
        start_iso = start.isoformat()
        end_iso = end.isoformat()

        defaults: Dict[str, Any] = {
            "month_name": month_name[month],
            "year": year,
            "level_start": settings.DEFAULT_LEVEL,
            "level_end": settings.DEFAULT_LEVEL,
            "words_learned": 0,
            "words_retained": 0,
            "retention_pct": 0.0,
            "quizzes_taken": 0,
            "avg_score": 0.0,
            "hours_watched": 0.0,
            "top_sources": [],
            "weak_areas": [],
        }
        try:
            with self.connect() as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT COUNT(*) as words_learned, COUNT(DISTINCT word) as unique_words "
                    "FROM word_logs WHERE user_id = ? AND logged_at >= ? AND logged_at < ?",
                    (user_id, start_iso, end_iso),
                )
                wrow = cur.fetchone() or {}

                cur.execute(
                    "SELECT COUNT(*) as quizzes_taken, AVG(score_pct) as avg_score "
                    "FROM quiz_results WHERE user_id = ? AND taken_at >= ? AND taken_at < ?",
                    (user_id, start_iso, end_iso),
                )
                qrow = cur.fetchone() or {}

                cur.execute(
                    "SELECT level FROM users WHERE id = ?",
                    (user_id,),
                )
                urow = cur.fetchone() or {}

            words_learned = int(wrow.get("words_learned") or 0)
            words_retained = int(wrow.get("unique_words") or 0)
            quizzes_taken = int(qrow.get("quizzes_taken") or 0)
            avg_raw = qrow.get("avg_score")
            avg_score = float(avg_raw) if avg_raw is not None else 0.0
            retention_pct = (words_retained / words_learned * 100.0) if words_learned > 0 else 0.0
            level = urow.get("level") or settings.DEFAULT_LEVEL

            return {
                "month_name": month_name[month],
                "year": year,
                "level_start": level,
                "level_end": level,
                "words_learned": words_learned,
                "words_retained": words_retained,
                "retention_pct": retention_pct,
                "quizzes_taken": quizzes_taken,
                "avg_score": avg_score,
                "hours_watched": 0.0,
                "top_sources": [],
                "weak_areas": [],
            }
        except Exception:
            return defaults

