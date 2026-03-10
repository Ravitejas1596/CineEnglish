from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from sentence_transformers import SentenceTransformer

from config import settings


class ChromaStore:
    """
    Chroma-backed memory with two collections:
    - user_conversations
    - vocabulary_bank
    Uses local sentence-transformers embeddings only.
    """

    def __init__(self, path: str | None = None, embedding_model: str | None = None) -> None:
        # Import chromadb lazily so environments without compatible pydantic
        # (e.g. Python 3.14 on Streamlit Cloud) don't fail at import time.
        try:  # pragma: no cover
            import chromadb  # type: ignore
        except Exception as e:
            raise RuntimeError("ChromaDB is not available in this environment.") from e

        path = path or settings.CHROMA_DB_PATH
        model = embedding_model or settings.EMBEDDING_MODEL

        self.client = chromadb.PersistentClient(path=path)
        self.embedder = SentenceTransformer(model)

        self.conv_collection = self.client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION_CONVERSATIONS
        )
        self.vocab_collection = self.client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION_VOCABULARY
        )

    def embed(self, text: str) -> List[float]:
        return self.embedder.encode(text).tolist()

    # Conversations -----------------------------------------------------
    def add_conversation(
        self,
        user_id: str,
        role: str,
        content: str,
        metadata: Dict[str, Any] | None = None,
    ) -> None:
        ts = datetime.utcnow().isoformat()
        doc_id = f"{user_id}_{role}_{ts}"
        meta: Dict[str, Any] = {"user_id": user_id, "role": role, "timestamp": ts}
        if metadata:
            meta.update(metadata)

        self.conv_collection.add(
            ids=[doc_id],
            documents=[content],
            embeddings=[self.embed(content)],
            metadatas=[meta],
        )

    def search_conversations(
        self,
        user_id: str,
        query: str,
        n_results: int = 5,
    ) -> List[Dict[str, Any]]:
        if not query.strip():
            return []

        try:
            res = self.conv_collection.query(
                query_embeddings=[self.embed(query)],
                n_results=n_results,
                where={"user_id": user_id},
            )
        except Exception:
            return []
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[]])[0]

        out: List[Dict[str, Any]] = []
        for doc, meta, dist in zip(docs, metas, dists):
            out.append(
                {
                    "content": doc,
                    "role": meta.get("role"),
                    "timestamp": meta.get("timestamp"),
                    "distance": dist,
                }
            )
        return out

    # Vocabulary --------------------------------------------------------
    def add_vocabulary(
        self,
        user_id: str,
        word: str,
        definition: str,
        scene: str,
        source_title: str,
        level: str,
    ) -> None:
        ts = datetime.utcnow().isoformat()
        doc_id = f"{user_id}_vocab_{word}_{ts}"
        document = f"{word}: {definition}. Context: {scene}"
        meta: Dict[str, Any] = {
            "user_id": user_id,
            "word": word,
            "definition": definition,
            "scene_context": scene,
            "source_title": source_title,
            "level": level,
            "timestamp": ts,
        }

        self.vocab_collection.add(
            ids=[doc_id],
            documents=[document],
            embeddings=[self.embed(document)],
            metadatas=[meta],
        )

    def search_vocabulary(
        self,
        user_id: str,
        query: str,
        n_results: int = 5,
    ) -> List[Dict[str, Any]]:
        if not query.strip():
            return []

        try:
            res = self.vocab_collection.query(
                query_embeddings=[self.embed(query)],
                n_results=n_results,
                where={"user_id": user_id},
            )
        except Exception:
            return []
        metas = res.get("metadatas", [[]])[0]

        out: List[Dict[str, Any]] = []
        for meta in metas:
            out.append(
                {
                    "word": meta.get("word"),
                    "definition": meta.get("definition"),
                    "scene_context": meta.get("scene_context"),
                    "source_title": meta.get("source_title"),
                }
            )
        return out

    def get_recent_vocabulary(
        self,
        user_id: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        try:
            res = self.vocab_collection.get(where={"user_id": user_id})
        except Exception:
            return []
        if not res or not res.get("ids"):
            return []
        metas = res.get("metadatas", []) or []
        sorted_metas = sorted(
            metas,
            key=lambda m: m.get("timestamp") or "",
            reverse=True,
        )[:limit]
        return sorted_metas

    def collection_stats(self, user_id: str) -> Dict[str, int]:
        conv = self.conv_collection.get(where={"user_id": user_id})
        vocab = self.vocab_collection.get(where={"user_id": user_id})
        return {
            "total_conversations": len(conv.get("ids", [])),
            "total_vocabulary": len(vocab.get("ids", [])),
        }


