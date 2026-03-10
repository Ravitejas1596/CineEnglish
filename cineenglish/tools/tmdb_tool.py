from __future__ import annotations

from typing import Any, Dict, List

import requests

from config import settings


class TMDBTool:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or settings.TMDB_API_KEY
        self.base_url = settings.TMDB_BASE_URL
        self.session = requests.Session()
        self.session.params.update({"api_key": self.api_key, "language": "en-US"})
        self.image_base = "https://image.tmdb.org/t/p/w500"

    # Helpers ----------------------------------------------------------
    def poster_url(self, path: str | None) -> str:
        if not path:
            return ""
        return f"{self.image_base}{path}"

    def _normalize_movie(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        release = raw.get("release_date") or ""
        year = release.split("-")[0] if release else ""
        return {
            "id": int(raw.get("id")),
            "title": raw.get("title") or raw.get("name") or "",
            "media_type": "movie",
            "overview": raw.get("overview") or "",
            "release_year": year,
            "rating": float(raw.get("vote_average") or 0.0),
            "vote_count": int(raw.get("vote_count") or 0),
            "poster_url": self.poster_url(raw.get("poster_path")),
            "genre_ids": raw.get("genre_ids") or [],
        }

    def _normalize_tv(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        first_air = raw.get("first_air_date") or ""
        year = first_air.split("-")[0] if first_air else ""
        return {
            "id": int(raw.get("id")),
            "title": raw.get("name") or raw.get("title") or "",
            "media_type": "series",
            "overview": raw.get("overview") or "",
            "release_year": year,
            "rating": float(raw.get("vote_average") or 0.0),
            "vote_count": int(raw.get("vote_count") or 0),
            "poster_url": self.poster_url(raw.get("poster_path")),
            "genre_ids": raw.get("genre_ids") or [],
        }

    # Public API -------------------------------------------------------
    def search_multi(self, query: str) -> List[Dict[str, Any]]:
        try:
            resp = self.session.get(
                f"{self.base_url}/search/multi",
                params={"query": query},
                timeout=15,
            )
            resp.raise_for_status()
        except Exception:
            return []

        data = resp.json()
        results: List[Dict[str, Any]] = []
        for item in data.get("results", []):
            mtype = item.get("media_type")
            if mtype == "movie":
                results.append(self._normalize_movie(item))
            elif mtype == "tv":
                results.append(self._normalize_tv(item))
        return results

    def get_movie_details(self, tmdb_id: int) -> Dict[str, Any]:
        try:
            resp = self.session.get(f"{self.base_url}/movie/{tmdb_id}", timeout=15)
            resp.raise_for_status()
        except Exception:
            return {}
        raw = resp.json()
        base = self._normalize_movie(raw)
        base.update(
            {
                "runtime_minutes": int(raw.get("runtime") or 0),
                "genres": [g.get("name") for g in raw.get("genres", [])],
                "tagline": raw.get("tagline") or "",
                "status": raw.get("status") or "",
            }
        )
        return base

    def get_series_details(self, tmdb_id: int) -> Dict[str, Any]:
        try:
            resp = self.session.get(f"{self.base_url}/tv/{tmdb_id}", timeout=15)
            resp.raise_for_status()
        except Exception:
            return {}
        raw = resp.json()
        base = self._normalize_tv(raw)
        base.update(
            {
                "first_air_year": base["release_year"],
                "number_of_seasons": int(raw.get("number_of_seasons") or 0),
                "number_of_episodes": int(raw.get("number_of_episodes") or 0),
                "genres": [g.get("name") for g in raw.get("genres", [])],
                "status": raw.get("status") or "",
            }
        )
        return base

    def get_similar(self, tmdb_id: int, media_type: str) -> List[Dict[str, Any]]:
        media = "movie" if media_type == "movie" else "tv"
        try:
            resp = self.session.get(
                f"{self.base_url}/{media}/{tmdb_id}/similar", timeout=15
            )
            resp.raise_for_status()
        except Exception:
            return []
        data = resp.json()
        items = data.get("results", [])[:5]
        norm: List[Dict[str, Any]] = []
        for item in items:
            if media == "movie":
                norm.append(self._normalize_movie(item))
            else:
                norm.append(self._normalize_tv(item))
        return norm

    def discover(
        self,
        media_type: str,
        genre_id: int,
        min_rating: float = 7.0,
        page: int = 1,
    ) -> List[Dict[str, Any]]:
        media = "movie" if media_type == "movie" else "tv"
        params = {
            "with_genres": genre_id,
            "sort_by": "popularity.desc",
            "vote_average.gte": min_rating,
            "vote_count.gte": 500,
            "page": page,
        }
        try:
            resp = self.session.get(
                f"{self.base_url}/discover/{media}", params=params, timeout=15
            )
            resp.raise_for_status()
        except Exception:
            return []
        data = resp.json()
        items = data.get("results", [])
        norm: List[Dict[str, Any]] = []
        for item in items:
            if media == "movie":
                norm.append(self._normalize_movie(item))
            else:
                norm.append(self._normalize_tv(item))
        return norm

