from __future__ import annotations

from dataclasses import dataclass
from typing import List

import requests

from config import settings


@dataclass
class RecommendationCard:
    title: str
    media_type: str
    genre: str
    rating: float
    overview: str
    poster_url: str
    cefr_band: str
    why_good_for_learning: str
    tmdb_id: int


class RecommenderAgent:
    def __init__(self, tmdb_api_key: str | None = None) -> None:
        self.api_key = tmdb_api_key or settings.TMDB_API_KEY
        self.base_url = settings.TMDB_BASE_URL
        self.genres = settings.SUPPORTED_GENRES

    def search_tmdb(self, media_type: str, genre_id: int, page: int = 1) -> list[dict]:
        endpoint = f"{self.base_url}/discover/{'movie' if media_type == 'movie' else 'tv'}"
        params = {
            "api_key": self.api_key,
            "with_genres": genre_id,
            "language": "en-US",
            "sort_by": "popularity.desc",
            "page": page,
        }
        try:
            resp = requests.get(endpoint, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            return data.get("results", []) or []
        except Exception:
            return []

    def get_recommendations(
        self,
        media_type: str,
        genre: str,
        level: str,
        mood: str = "",
        liked: str = "",
    ) -> List[RecommendationCard]:
        genre_id = self.genres.get(genre)
        if not genre_id:
            return []

        results = self.search_tmdb(media_type, genre_id, page=1)
        filtered = [
            r
            for r in results
            if (r.get("vote_average") or 0) >= 7.0 and (r.get("vote_count") or 0) >= 500
        ][:5]

        cefr_band = level or settings.DEFAULT_LEVEL
        why_map = {
            "Drama": "Rich emotional vocabulary and natural conversation flow.",
            "Comedy": "Casual speech, idioms, and everyday expressions.",
            "Crime & Thriller": "Legal and investigative vocabulary, complex dialogue.",
            "Sci-Fi": "Technical vocabulary and speculative language.",
            "Action": "Direct commands and high-energy short sentences.",
        }
        why_default = "Good balance of clear dialogue and engaging story."

        cards: List[RecommendationCard] = []
        for r in filtered:
            title = r.get("title") or r.get("name") or "Unknown"
            rating = float(r.get("vote_average") or 0.0)
            overview = (r.get("overview") or "No description available.")[:300]
            tmdb_id = int(r.get("id"))
            poster_path = r.get("poster_path") or ""
            poster_url = (
                f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else ""
            )

            why = why_map.get(genre, why_default)
            if mood:
                why += f" Mood: {mood}."
            if liked:
                why += f" Chosen to complement what you liked about {liked}."

            cards.append(
                RecommendationCard(
                    title=title,
                    media_type=media_type,
                    genre=genre,
                    rating=rating,
                    overview=overview,
                    poster_url=poster_url,
                    cefr_band=cefr_band,
                    why_good_for_learning=why,
                    tmdb_id=tmdb_id,
                )
            )
        return cards

