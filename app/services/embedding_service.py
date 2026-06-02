"""
Embedding Service — handles model loading and embedding generation.
Uses sentence-transformers/all-MiniLM-L6-v2 (384 dimensions).
Stores embeddings in Qdrant (local file storage).

KEY: Prepends section_title to content before encoding so the model
     "sees" the heading — this dramatically improves retrieval for
     heading-specific queries like "sick leave".
"""

from typing import List
from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models.document import Chunk, DocumentVersion, LifecycleState, Document
from app.repositories.embedding_repository import EmbeddingRepository


# ── Singleton model loader ──────────────────────────────────────
_model = None


def _get_model():
    """Lazy-load the sentence-transformers model once."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _model


class EmbeddingService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = EmbeddingRepository()
        self.model = _get_model()

    def embed_version(self, version_id: UUID) -> dict:
        """
        Generate and store embeddings for all chunks of an approved version.
        
        KEY CHANGE: Prepends section_title to content before encoding.
        "Sick Leave Policy: Employees are entitled to 10 days..."
        instead of just "Employees are entitled to 10 days..."
        """
        version = (
            self.db.query(DocumentVersion)
            .filter(DocumentVersion.id == version_id)
            .first()
        )

        if not version:
            raise ValueError(f"Version {version_id} not found")
        if version.lifecycle_state != LifecycleState.APPROVED:
            raise ValueError(f"Version {version_id} is not APPROVED — cannot embed")

        document = (
            self.db.query(Document)
            .filter(Document.id == version.document_id)
            .first()
        )

        chunks = (
            self.db.query(Chunk)
            .filter(Chunk.version_id == version_id)
            .order_by(Chunk.chunk_index)
            .all()
        )

        if not chunks:
            raise ValueError(f"No chunks found for version {version_id}")

        # Delete old embeddings
        self.repo.delete_by_version(version_id)

        # Generate embeddings — PREPEND section_title for stronger heading signal
        texts = []
        for chunk in chunks:
            title = chunk.section_title or f"Section {chunk.chunk_index}"
            # Format: "Sick Leave Policy: Employees are entitled to..."
            embedding_text = f"{title}: {chunk.content}"
            texts.append(embedding_text)

        embeddings = self.model.encode(texts, show_progress_bar=False)

        # Store each embedding with full metadata
        for chunk, embedding_vector in zip(chunks, embeddings):
            # Parse keywords from chunk if stored, otherwise extract
            keywords = []
            if hasattr(chunk, '_keywords_cache'):
                keywords = chunk._keywords_cache
            else:
                # Fall back to extracting from content
                from app.utils.file_parser import extract_keywords
                title = chunk.section_title or f"Section {chunk.chunk_index}"
                keywords = extract_keywords(title, chunk.content)

            self.repo.store_embedding(
                chunk_id=chunk.id,
                version_id=version_id,
                document_id=version.document_id,
                document_title=document.title,
                version_number=version.version_number,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                section_title=chunk.section_title or f"Section {chunk.chunk_index}",
                section_number=chunk.section_number or str(chunk.chunk_index),
                keywords=keywords,
                lifecycle_state=version.lifecycle_state.value,
                embedding=embedding_vector.tolist()
            )

        # Update embedding metadata on the version
        version.embedding_metadata = {
            "model": "all-MiniLM-L6-v2",
            "dimension": 384,
            "chunk_count": len(chunks),
            "prepend_title": True,
            "embedded_at": datetime.now(timezone.utc).isoformat()
        }
        self.db.flush()

        return {
            "version_id": str(version_id),
            "chunks_embedded": len(chunks),
            "model": "all-MiniLM-L6-v2"
        }

    def embed_query(self, query_text: str) -> List[float]:
        """Encode a query string into a 384-dim vector."""
        embedding = self.model.encode(query_text, show_progress_bar=False)
        return embedding.tolist()
