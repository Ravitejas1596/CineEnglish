from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

from config import settings


@dataclass(frozen=True)
class DictionaryEntry:
    word: str
    phonetic: str | None
    part_of_speech: str | None
    definition: str | None
    example: str | None


class DictionaryTool:
    def lookup(self, word: str) -> DictionaryEntry | None:
        word = word.strip().lower()
        if not word:
            return None

        url = f"{settings.FREE_DICTIONARY_API_BASE}/{word}"
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code != 200:
                return None
            data: list[dict[str, Any]] = resp.json()
        except Exception:
            return None

        if not data:
            return None

        entry = data[0]
        phonetic = entry.get("phonetic")

        meanings = entry.get("meanings") or []
        if meanings:
            m0 = meanings[0]
            pos = m0.get("partOfSpeech")
            defs = m0.get("definitions") or []
            if defs:
                d0 = defs[0]
                definition = d0.get("definition")
                example = d0.get("example")
            else:
                definition, example, pos = None, None, None
        else:
            pos = definition = example = None

        return DictionaryEntry(
            word=word,
            phonetic=phonetic,
            part_of_speech=pos,
            definition=definition,
            example=example,
        )

