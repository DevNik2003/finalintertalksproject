"""
Embedding Repository — Qdrant vector database layer.
Stores chunk embeddings with full metadata (content, keywords, section info).
Searches with APPROVED-only filter and returns payload for re-ranking.
"""

from typing import List, Dict, Any
from uuid import UUID
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue
)

from app.core.config import settings


# ── Singleton Qdrant client ─────────────────────────────────────
_qdrant_client = None
COLLECTION_NAME = "chunk_embeddings"
VECTOR_DIM = 384


def _get_qdrant_client() -> QdrantClient:
    """Lazy-initialize the Qdrant client with local file storage."""
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClient(path=settings.QDRANT_STORAGE_PATH)
        _ensure_collection_exists(_qdrant_client)
    return _qdrant_client


def _ensure_collection_exists(client: QdrantClient):
    """Create the chunk_embeddings collection if it doesn't exist."""
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in collections:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_DIM,
                distance=Distance.COSINE
            )
        )


class EmbeddingRepository:
    def __init__(self):
        self.client = _get_qdrant_client()

    def store_embedding(
        self,
        chunk_id:str,
        version_id: str,
        document_id: str,
        document_title: str,
        version_number: int,
        chunk_index: int,
        content: str,
        section_title: str,
        section_number: str,
        keywords: List[str],
        lifecycle_state: str,
        embedding: List[float]
    ):
        """
        Store a single chunk embedding in Qdrant with full metadata payload.
        Keywords are stored for keyword-based re-ranking during retrieval.
        """
        point = PointStruct(
            id=str(chunk_id),
            vector=embedding,
            payload={
                "chunk_id": str(chunk_id),
                "version_id": str(version_id),
                "document_id": str(document_id),
                "document_title": document_title,
                "version_number": version_number,
                "chunk_index": chunk_index,
                "content": content,
                "section_title": section_title or f"Section {chunk_index}",
                "section_number": section_number or str(chunk_index),
                "keywords": keywords or [],
                "lifecycle_state": lifecycle_state
            }
        )
        self.client.upsert(
            collection_name=COLLECTION_NAME,
            points=[point]
        )

    def delete_by_version(self, version_id: str) -> None:
        """Delete all embeddings for a given version (used before re-embedding)."""
        self.client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="version_id",
                        match=MatchValue(value=str(version_id))
                    )
                ]
            )
        )

    def search_similar(
        self,
        query_embedding: List[float],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search chunk embeddings using cosine similarity.
        Only returns chunks from APPROVED document versions.
        Returns MORE results (limit=10) for re-ranking in query service.
        """
        response = self.client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_embedding,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="lifecycle_state",
                        match=MatchValue(value="APPROVED")
                    )
                ]
            ),
            limit=limit,
            with_payload=True
        )
        results=response.points

        return [
            {
                "chunk_id": hit.payload["chunk_id"],
                "content": hit.payload["content"],
                "chunk_index": hit.payload["chunk_index"],
                "document_id": hit.payload["document_id"],
                "version_id": hit.payload["version_id"],
                "document_title": hit.payload["document_title"],
                "version_number": hit.payload["version_number"],
                "section_title": hit.payload.get("section_title", f"Section {hit.payload['chunk_index']}"),
                "section_number": hit.payload.get("section_number", str(hit.payload['chunk_index'])),
                "keywords": hit.payload.get("keywords", []),
                "similarity": float(hit.score)
            }
            for hit in results
        ]