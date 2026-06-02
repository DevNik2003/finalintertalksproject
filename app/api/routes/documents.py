from typing import Any, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Form, Query, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
import os

from app.core.database import get_db
from app.core.config import settings
from app.core.dependencies import require_role, get_current_user
from app.models.user import User, UserRole
from app.schemas.document import DocumentUploadResponse, DocumentApproveResponse, DocumentOut
from app.services.document_service import DocumentService
from app.repositories.document_repository import DocumentRepository
from app.repositories.user_repository import UserRepository
from jose import jwt, JWTError

router = APIRouter()

@router.get("/", response_model=List[DocumentOut])
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.VIEWER, UserRole.CONTRIBUTOR, UserRole.REVIEWER))
):
    """
    List all documents with their versions.
    Accessible by all authenticated users.
    """
    repo = DocumentRepository(db)
    return repo.get_all_documents()

@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
def upload_document(
    file: UploadFile = File(...),
    department: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CONTRIBUTOR))
) -> Any:
    """
    Upload a document (PDF or DOCX), assign to a department.
    Requires CONTRIBUTOR or ADMIN role.
    """
    service = DocumentService(db)
    return service.upload_document(file, department, current_user)

@router.post("/{version_id}/approve", response_model=DocumentApproveResponse)
def approve_document(
    version_id:str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.REVIEWER))
) -> Any:
    """
    Approve an uploaded document version.
    Triggers chunking.
    Requires REVIEWER or ADMIN role.
    """
    service = DocumentService(db)
    return service.approve_document(version_id, current_user)

@router.get("/{version_id}/view", response_class=FileResponse)
def view_document_file(
    version_id: str,
    db: Session = Depends(get_db),
    token: Optional[str] = Query(None),
) -> Any:
    """
    Download/view the original document for the given version.
    Accepts auth via ?token= query param (for new-tab file viewing).
    """
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required. Pass ?token= query param.")
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        user_repo = UserRepository(db)
        current_user = user_repo.get_user_by_id(user_id)
        if not current_user or not current_user.is_active:
            raise HTTPException(status_code=401, detail="Invalid or inactive user")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    service = DocumentService(db)
    file_path = service.get_document_file(version_id, current_user)
    
    filename = os.path.basename(file_path)
    original_filename = "_".join(filename.split("_")[1:]) if "_" in filename else filename
    
    return FileResponse(path=file_path, filename=original_filename)


@router.post("/{version_id}/reembed")
def reembed_document(
    version_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.REVIEWER))
) -> Any:
    """
    Re-chunk and re-embed an approved document version using section-based chunking.
    Admin/Reviewer only. Use after upgrading the chunking strategy.
    """
    from app.utils.file_parser import split_into_sections
    from app.services.embedding_service import EmbeddingService
    from app.models.document import DocumentVersion, LifecycleState, Chunk

    repo = DocumentRepository(db)
    version = repo.get_version_by_id(version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    if version.lifecycle_state != LifecycleState.APPROVED:
        raise HTTPException(status_code=400, detail="Only APPROVED versions can be re-embedded")

    # Delete old chunks from PostgreSQL
    db.query(Chunk).filter(Chunk.version_id == version_id).delete()
    db.flush()

    # Re-chunk with section-based strategy
    chunks_data = split_into_sections(version.raw_text)
    repo.create_chunks(version_id, chunks_data)

    # Update chunking config
    version.chunking_config = {
        "strategy": "section-based",
        "max_section_words": 600,
        "chunk_count": len(chunks_data),
        "re_embedded": True,
        "re_embedded_by": str(current_user.id)
    }

    # Re-embed
    embedding_svc = EmbeddingService(db)
    result = embedding_svc.embed_version(version_id)

    db.commit()

    return {
        "message": "Re-embedded successfully",
        "version_id": str(version_id),
        "chunks_created": len(chunks_data),
        "embeddings_stored": result["chunks_embedded"]
    }
