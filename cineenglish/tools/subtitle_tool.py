from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal

from youtube_transcript_api import YouTubeTranscriptApi


LanguageCode = str  # e.g. "en", "en-US"
SourceType = Literal["file", "youtube"]


@dataclass(frozen=True)
class SubtitleSegment:
    start: float  # seconds
    end: float    # seconds
    text: str


class SubtitleTool:
    """
    Unified interface over:
    - `subliminal`  for local media files (multi-provider subtitles)
    - `youtube-transcript-api` for YouTube videos (no API key needed)
    """

    def for_youtube(self, video_id: str, languages: Iterable[LanguageCode] = ("en",)) -> list[SubtitleSegment]:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # Pick the first matching language (auto-translated ok as fallback)
        for lang in languages:
            try:
                t = transcript_list.find_transcript([lang])
                raw = t.fetch()
                break
            except Exception:
                continue
        else:
            # Fallback: first available transcript
            t = transcript_list.find_manually_created_transcript([tr.language_code for tr in transcript_list])
            raw = t.fetch()

        segments: list[SubtitleSegment] = []
        for item in raw:
            start = float(item.get("start", 0.0))
            dur = float(item.get("duration", 0.0))
            text = item.get("text", "").replace("\n", " ").strip()
            if not text:
                continue
            segments.append(
                SubtitleSegment(
                    start=start,
                    end=start + dur,
                    text=text,
                )
            )
        return segments

    def for_file(self, video_path: str, languages: Iterable[LanguageCode] = ("en",)) -> list[SubtitleSegment]:
        """
        Use `subliminal` to download/parse subtitles for a local media file.
        NOTE: this assumes the file exists on disk on the server running CineEnglish.
        """
        from pathlib import Path

        from babelfish import Language
        from subliminal import Video, download_best_subtitles, region

        path = Path(video_path)
        if not path.exists():
            raise FileNotFoundError(video_path)

        # Configure a simple in-memory cache
        region.configure("dogpile.cache.memory")

        video = Video.fromname(str(path))
        langs = {Language(lang) for lang in languages}

        subs_map = download_best_subtitles({video}, langs)
        subs = subs_map.get(video) or set()
        if not subs:
            return []

        # Take best subtitle for the first requested language available
        picked = None
        for lang in languages:
            for s in subs:
                if str(s.language) == lang or s.language.alpha2 == lang:
                    picked = s
                    break
            if picked:
                break
        if picked is None:
            picked = next(iter(subs))

        # Parse into segments
        content = picked.content
        try:
            # If subliminal returned a pysubs2 object
            events = list(content)
        except TypeError:
            # Or raw text; return a single segment
            return [SubtitleSegment(start=0.0, end=0.0, text=str(content))]

        segments: list[SubtitleSegment] = []
        for e in events:
            text = str(getattr(e, "text", "")).replace("\n", " ").strip()
            if not text:
                continue
            # pysubs2 stores milliseconds
            start_s = getattr(e, "start", 0) / 1000.0
            end_s = getattr(e, "end", 0) / 1000.0
            segments.append(SubtitleSegment(start=start_s, end=end_s, text=text))

        return segments

