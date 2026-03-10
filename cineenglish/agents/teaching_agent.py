from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List

from groq import Groq

from config import settings
from cineenglish.agents.subtitle_agent import VocabItem


@dataclass
class QuizQuestion:
    question: str
    options: List[str]
    correct: str
    word: str
    explanation: str


class TeachingAgent:
    def __init__(self, groq_client: Groq | None = None) -> None:
        # Groq client is optional; when unavailable we fall back to local quiz generation.
        self.client = groq_client
        self.model = settings.GROQ_MODEL

    # --- Core quiz builders -------------------------------------------
    def build_quiz(self, vocab_items: List[VocabItem], level: str) -> List[QuizQuestion]:
        payload = [
            {
                "word": v.word,
                "definition": v.definition,
                "scene_context": v.scene_context,
                "level": level,
            }
            for v in vocab_items
        ]
        return self._call_quiz_llm(payload)

    def rebuild_quiz_from_words(
        self, words: List[Dict[str, Any]], level: str
    ) -> List[QuizQuestion]:
        payload = [
            {
                "word": w.get("word"),
                "definition": w.get("definition", ""),
                "scene_context": w.get("scene_context", ""),
                "level": level,
            }
            for w in words
        ]
        return self._call_quiz_llm(payload)

    def _call_quiz_llm(self, payload: List[Dict[str, Any]]) -> List[QuizQuestion]:
        if not payload:
            return []

        system_prompt = (
            "You are an English teacher building multiple choice quizzes.\n"
            "Given a list of words with definitions and scene context, "
            "create one multiple choice question per word.\n"
            "Each question should test understanding in context, not just the dictionary definition.\n"
            "Return ONLY a JSON array, no markdown, no explanation.\n"
            "JSON format for each item:\n"
            '{'
            '"question": str, '
            '"options": [str, str, str, str], '
            '"correct": "A" | "B" | "C" | "D", '
            '"word": str, '
            '"explanation": str'
            "}"
        )

        user_prompt = (
            "Build quiz questions for these vocabulary items:\n"
            f"{json.dumps(payload, ensure_ascii=False)}"
        )

        if self.client is None:
            raw = self._fallback_quiz(payload)
        else:
            try:
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    max_tokens=settings.GROQ_MAX_TOKENS,
                    temperature=0.4,
                )
                content = resp.choices[0].message.content or "[]"
                raw_text = content.strip()
                if raw_text.startswith("```"):
                    parts = raw_text.split("```")
                    if len(parts) > 1:
                        raw_text = parts[1]
                    if raw_text.lstrip().startswith("json"):
                        raw_text = raw_text.lstrip()[4:]
                raw_text = raw_text.strip()
                raw = json.loads(raw_text)
            except Exception:
                raw = self._fallback_quiz(payload)

        questions: List[QuizQuestion] = []
        for item in raw:
            try:
                q = QuizQuestion(
                    question=str(item.get("question", "")),
                    options=[str(o) for o in (item.get("options") or [])][:4],
                    correct=str(item.get("correct", "A")),
                    word=str(item.get("word", "")),
                    explanation=str(item.get("explanation", "")),
                )
                if len(q.options) == 4:
                    questions.append(q)
            except Exception:
                continue
        return questions

    def _fallback_quiz(self, payload: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Build simple multiple-choice questions locally if Groq or JSON fails.
        """
        out: List[Dict[str, Any]] = []
        definitions = [p.get("definition", "") or "" for p in payload]
        for idx, item in enumerate(payload):
            word = item.get("word", "")
            definition = item.get("definition", "") or f"The meaning of {word}."
            scene = item.get("scene_context", "")
            question = f"What is the meaning of '{word}' in this context: {scene}"

            # Pick wrong options from other definitions
            wrong_defs = [d for j, d in enumerate(definitions) if j != idx and d]
            while len(wrong_defs) < 3:
                wrong_defs.append("An unrelated meaning.")
            wrong_opts = wrong_defs[:3]

            options = [definition] + wrong_opts
            out.append(
                {
                    "question": question,
                    "options": options,
                    "correct": "A",
                    "word": word,
                    "explanation": f"{word} means: {definition}",
                }
            )
        return out

    # --- Lesson tips --------------------------------------------------
    def generate_lesson_tip(
        self, word: str, definition: str, scene: str, level: str
    ) -> str:
        prompt = (
            f"Word: {word}\n"
            f"Definition: {definition}\n"
            f"Scene: {scene}\n"
            f"Level: {level}\n\n"
            "Give a 2-sentence tip to remember and use this word naturally. "
            "Be simple and encouraging."
        )
        if self.client is None:
            return f"Try to notice '{word}' in more scenes and repeat it aloud a few times."

        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a friendly English teacher.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=120,
                temperature=0.5,
            )
            return resp.choices[0].message.content or ""
        except Exception:
            return f"Try to notice '{word}' in more scenes and repeat it aloud a few times."


