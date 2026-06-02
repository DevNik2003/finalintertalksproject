"""
Query API Route — POST /api/v1/query

Validates user role (VIEWER and above), executes the retrieval pipeline,
and returns either a grounded answer with citations or a refusal.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_role
from app.models.user import User, UserRole
from app.schemas.query import QueryRequest, QueryResponse
from app.services.query_service import QueryService

router = APIRouter()


@router.post("/", response_model=QueryResponse)
def execute_query(
    request: QueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.VIEWER, UserRole.CONTRIBUTOR, UserRole.REVIEWER))
):
    """
    Execute a semantic search query against approved document content.

    - User must be active with VIEWER role or above
    - Only searches APPROVED document versions
    - Applies similarity threshold (0.65)
    - Detects conflicting sources
    - Returns grounded answer with citations, or refuses with reason
    """
    service = QueryService(db)
    result = service.execute_query(request.query, current_user)
    return QueryResponse(**result)
