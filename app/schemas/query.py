"""Pydantic schemas for the query/retrieval endpoint."""

import uuid
from typing import Optional, List
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """User's search query."""
    query: str = Field(..., min_length=1, max_length=1000, description="The search query text")


class Citation(BaseModel):
    """A single citation referencing the source chunk."""
    document: str
    version: int
    section: str
    section_number: Optional[str] = None
    chunk_id: str
    similarity: float


class QueryResponse(BaseModel):
    """Successful query response with answer and citations."""
    status: str  # "success" or "refused"
    reason: Optional[str] = None
    answer: Optional[str] = None
    citations: List[Citation] = []
