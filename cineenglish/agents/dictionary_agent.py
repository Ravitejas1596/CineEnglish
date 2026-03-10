from __future__ import annotations

import time
from typing import Any, Dict, List

import requests

from config import settings


class DictionaryAgent:
    """
    Thin wrapper around the Free Dictionary API.
    No LLMs here – just HTTP + parsing.
    """

    def __init__(self) -> None:
        self.base_url = settings.DICTIONARY_API_URL

    def lookup(self, word: str) -> Dict[str, Any]:
        word_clean = word.strip()
        if not word_clean:
            return {"word": word, "definition": "", "error": "empty word"}

        url = f"{self.base_url}/{word_clean}"
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code != 200:
                return {"word": word_clean, "definition": "", "error": "not found"}
            data = resp.json()
        except Exception:
            return {"word": word_clean, "definition": "", "error": "not found"}

        if not isinstance(data, list) or not data:
            return {"word": word_clean, "definition": "", "error": "not found"}

        entry = data[0]
        phonetic = entry.get("phonetic", "")
        meanings = entry.get("meanings") or []
        definition = ""
        part_of_speech = ""
        example = ""

        if meanings:
            m0 = meanings[0]
            part_of_speech = m0.get("partOfSpeech") or ""
            defs = m0.get("definitions") or []
            if defs:
                d0 = defs[0]
                definition = d0.get("definition") or ""
                example = d0.get("example") or ""

        audio_url = ""
        phonetics = entry.get("phonetics") or []
        for p in phonetics:
            if p.get("audio"):
                audio_url = p["audio"]
                break

        return {
            "word": word_clean,
            "phonetic": phonetic,
            "definition": definition,
            "part_of_speech": part_of_speech,
            "example": example,
            "audio_url": audio_url,
        }

    def bulk_lookup(self, words: List[str]) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for w in words:
            info = self.lookup(w)
            if not info.get("error") and info.get("definition"):
                results.append(info)
            time.sleep(0.2)
        return results


