from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from app.models.document import Document, DocumentVersion, Chunk, AuditLog, LifecycleState

class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_document_by_id(self, document_id: str) -> Optional[Document]:
        return self.db.query(Document).filter(Document.id == document_id).first()

    def get_all_documents(self) -> List[Document]:
        from sqlalchemy.orm import joinedload
        return self.db.query(Document).options(joinedload(Document.versions)).all()

    def get_version_by_checksum(self, checksum: str) -> Optional[DocumentVersion]:
        return self.db.query(DocumentVersion).filter(DocumentVersion.checksum == checksum).first()

    def get_version_by_id(self, version_id: str) -> Optional[DocumentVersion]:
        return self.db.query(DocumentVersion).filter(DocumentVersion.id == version_id).first()

    def get_latest_version_number(self, document_id: str) -> int:
        version = self.db.query(DocumentVersion)\
            .filter(DocumentVersion.document_id == document_id)\
            .order_by(DocumentVersion.version_number.desc())\
            .first()
        return version.version_number if version else 0

    def create_document(self, title: str, department: str, created_by: str) -> Document:
        db_doc = Document(
            title=title,
            department=department,
            created_by=created_by
        )
        self.db.add(db_doc)
        self.db.flush() # Flush to get the ID without committing
        return db_doc

    def create_version(self, document_id: str, version_number: int, checksum: str, 
                       file_path: str, raw_text: str, uploaded_by: str) -> DocumentVersion:
        
        db_version = DocumentVersion(
            document_id=document_id,
            version_number=version_number,
            checksum=checksum,
            file_path=file_path,
            raw_text=raw_text,
            uploaded_by=uploaded_by,
            lifecycle_state=LifecycleState.UPLOADED
        )
        self.db.add(db_version)
        try:
            self.db.flush()
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=400, detail="Database integrity error. Checksum or version combination may already exist.")
        return db_version

    def update_version_state(self, version_id: str, state: LifecycleState, approved_by: Optional[str] = None) -> DocumentVersion:
        db_version = self.get_version_by_id(version_id)
        if not db_version:
            raise HTTPException(status_code=404, detail="Version not found")
            
        db_version.lifecycle_state = state
        if approved_by:
            db_version.approved_by = approved_by
            from datetime import datetime, timezone
            db_version.approved_at = datetime.now(timezone.utc)
            
        self.db.flush()
        return db_version
        
    def create_chunks(self, version_id: str, chunks_data: List[Dict[str, Any]]):
        db_chunks = []
        for i, chunk_data in enumerate(chunks_data):
            db_chunk = Chunk(
                version_id=version_id,
                chunk_index=i,
                content=chunk_data['content'],
                section_title=chunk_data.get('section_title'),
                section_number=chunk_data.get('section_number'),
                token_count=chunk_data.get('token_count')
            )
            db_chunks.append(db_chunk)
            self.db.add(db_chunk)
        self.db.flush()
        return db_chunks

    def log_audit(self, action_type: str, user_id: str, document_id: str, version_id: str, metadata: Dict[str, Any] = None) -> AuditLog:
        db_log = AuditLog(
            action_type=action_type,
            user_id=user_id,
            document_id=document_id,
            version_id=version_id,
            metadata=metadata
        )
        self.db.add(db_log)
        self.db.flush()
        return db_log
