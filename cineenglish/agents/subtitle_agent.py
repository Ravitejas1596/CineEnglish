from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

from youtube_transcript_api import YouTubeTranscriptApi

from config import settings
from cineenglish.agents.dictionary_agent import DictionaryAgent
from cineenglish.database.sqlite_db import SqliteDB


@dataclass
class VocabItem:
    word: str
    definition: str
    scene_context: str
    source_title: str
    level: str
    part_of_speech: str = ""


class SubtitleAgent:
    """
    Fetch subtitles from YouTube or local files, mine candidate vocabulary,
    enrich with dictionary data, and return VocabItem objects.
    """

    def __init__(self, db: SqliteDB | None = None) -> None:
        self.db = db or SqliteDB()
        self.dictionary = DictionaryAgent()
        self.stop_words = set(settings.STOP_WORDS)
        self.min_len = settings.MIN_WORD_LENGTH
        self.max_vocab = settings.MAX_VOCAB_PER_SESSION

    # --- Fetchers -----------------------------------------------------
    def fetch_youtube(self, video_id: str) -> str:
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
        except Exception as e:  # pragma: no cover
            raise ValueError(f"Could not fetch YouTube transcript: {e}") from e

        text = " ".join(chunk.get("text", "") for chunk in transcript)
        return self._clean_text(text)

    def fetch_file(self, file_path: str, title: str) -> str:
        try:
            from pathlib import Path

            from babelfish import Language
            from subliminal import Video, download_best_subtitles, region

            path = Path(file_path)
            if not path.exists():
                raise ValueError(f"File not found: {file_path}")

            region.configure("dogpile.cache.memory")
            video = Video.fromname(str(path))
            subs = download_best_subtitles({video}, {Language("eng")}).get(video) or set()
            if not subs:
                raise ValueError("No subtitles found for this file.")
            subtitle = next(iter(subs))
            content = subtitle.content
            if hasattr(content, "events"):
                # pysubs2-like object
                lines = [e.text for e in content.events if getattr(e, "text", "").strip()]
                text = " ".join(lines)
            else:
                text = str(content)
        except Exception as e:  # pragma: no cover
            raise ValueError(f"Could not fetch subtitles for file '{title}': {e}") from e

        return self._clean_text(text)

    # --- Core processing ----------------------------------------------
    def extract_vocab(self, text: str, level: str, source_title: str) -> List[VocabItem]:
        sentences = re.split(r"(?<=[.!?])\s+", text)
        word_scores: dict[str, float] = {}
        word_sentence: dict[str, str] = {}

        basic_words = {
            "time",
            "person",
            "year",
            "day",
            "man",
            "woman",
            "child",
            "thing",
            "world",
            "school",
        }  # tiny stand-in for basic 1000 list

        for sent in sentences:
            lowered = sent.lower()
            for raw in re.findall(r"[A-Za-z']+", lowered):
                w = raw.strip("'")
                if (
                    len(w) < self.min_len
                    or w in self.stop_words
                    or not w.isalpha()
                    or w in basic_words
                ):
                    continue
                score = len(w)
                word_scores[w] = max(word_scores.get(w, 0), score)
                word_sentence.setdefault(w, sent.strip())

        # pick top N by score
        sorted_words = sorted(word_scores.items(), key=lambda kv: kv[1], reverse=True)
        selected = [w for w, _ in sorted_words[: self.max_vocab]]

        try:
            lookups = self.dictionary.bulk_lookup(selected)
            dict_results = {d["word"]: d for d in lookups}
        except Exception:
            dict_results = {}

        items: List[VocabItem] = []
        for w in selected:
            info = dict_results.get(w, {})
            items.append(
                VocabItem(
                    word=w,
                    definition=info.get("definition", ""),
                    scene_context=word_sentence.get(w, ""),
                    source_title=source_title,
                    level=level,
                    part_of_speech=info.get("part_of_speech", ""),
                )
            )
        return items

    def process_youtube(
        self, video_id: str, source_title: str, level: str, user_id: str
    ) -> List[VocabItem]:
        vid = self.extract_video_id(video_id)
        text = self.fetch_youtube(vid)
        items = self.extract_vocab(text, level=level, source_title=source_title)
        self._log_words(user_id, items, source_type="youtube")
        return items

    def process_file(
        self, file_path: str, source_title: str, level: str, user_id: str
    ) -> List[VocabItem]:
        text = self.fetch_file(file_path, title=source_title)
        items = self.extract_vocab(text, level=level, source_title=source_title)
        self._log_words(user_id, items, source_type="file")
        return items

    # --- Helpers ------------------------------------------------------
    def _clean_text(self, text: str) -> str:
        text = text.replace("\n", " ")
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _log_words(self, user_id: str, items: List[VocabItem], source_type: str) -> None:
        payload = [
            {
                "word": v.word,
                "definition": v.definition,
                "scene_context": v.scene_context,
                "source_title": v.source_title,
                "source_type": source_type,
            }
            for v in items
        ]
        self.db.log_words(user_id=user_id, words=payload)

    def extract_video_id(self, url_or_id: str) -> str:
        import re

        patterns = [
            r"(?:v=)([a-zA-Z0-9_-]{11})",
            r"(?:youtu\\.be/)([a-zA-Z0-9_-]{11})",
        ]
        for pattern in patterns:
            match = re.search(pattern, url_or_id)
            if match:
                return match.group(1)
        return url_or_id.strip()


