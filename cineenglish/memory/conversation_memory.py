from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

from cineenglish.memory.chroma_store import ChromaStore


@dataclass
class Message:
    role: str
    content: str


class ConversationMemory:
    """
    Handles short-term and semantic memory for a single user session.
    """

    def __init__(self, chroma_store: ChromaStore | None, user_id: str) -> None:
        self.chroma_store = chroma_store
        self.user_id = user_id
        self.short_term: List[Message] = []
        self.session_start = datetime.utcnow()

    def add_message(self, role: str, content: str) -> None:
        self.short_term.append(Message(role=role, content=content))
        # Trim to last 20 messages
        if len(self.short_term) > 20:
            self.short_term = self.short_term[-20:]

        # Persist to Chroma if available
        if self.chroma_store is not None:
            self.chroma_store.add_conversation(
                user_id=self.user_id,
                role=role,
                content=content,
            )

    def get_short_term(self) -> List[Dict[str, str]]:
        return [{"role": m.role, "content": m.content} for m in self.short_term]

    def get_relevant_context(self, query: str, n: int = 3) -> str:
        if self.chroma_store is None:
            return ""

        hits = self.chroma_store.search_conversations(
            user_id=self.user_id, query=query, n_results=n
        )
        if not hits:
            return ""
        lines = ["Relevant past context:"]
        for h in hits:
            role = h.get("role", "user")
            content = h.get("content", "")
            lines.append(f"- [{role}] {content}")
        return "\n".join(lines)

    def build_groq_messages(
        self,
        system_prompt: str,
        new_user_message: str,
    ) -> List[Dict[str, str]]:
        msgs: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
        # last 10 short-term messages
        for m in self.short_term[-10:]:
            msgs.append({"role": m.role, "content": m.content})
        msgs.append({"role": "user", "content": new_user_message})
        return msgs

    def clear_session(self) -> None:
        self.short_term = []
        self.session_start = datetime.utcnow()

    def session_summary(self) -> Dict[str, object]:
        duration_minutes = (datetime.utcnow() - self.session_start).total_seconds() / 60.0
        return {
            "message_count": len(self.short_term),
            "session_duration_minutes": duration_minutes,
            "session_start": self.session_start.isoformat(),
        }

