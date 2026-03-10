from __future__ import annotations

from functools import lru_cache

from langchain_groq import ChatGroq

from config import settings


@lru_cache(maxsize=1)
def get_llm() -> ChatGroq:
    """
    Shared Groq-backed chat model for all agents.
    """
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model=settings.GROQ_MODEL,
        temperature=0.4,
    )

