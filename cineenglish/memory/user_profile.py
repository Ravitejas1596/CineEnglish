from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class UserProfile:
    user_id: str = "default"
    cefr_level: str = "B1"
    streak_days: int = 0
    weak_areas: list[str] = field(default_factory=list)

