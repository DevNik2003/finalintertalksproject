from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.repositories.document_repository import DocumentRepository
from app.models.user import User
from app.models.document import LifecycleState
from app.utils.file_parser import extract_pdf, extract_docx, generate_checksum, split_into_chunks
from app.utils.storage import save_upload_file, delete_stored_file

class DocumentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = DocumentRepository(db)

    def upload_document(self, file: UploadFile, department: str, current_user: User):
        """
        Handles the document upload pipeline:
        1. Validate file
        2. Extract Text
        3. Determine Duplicate status
        4. Save to Storage
        5. Create DB Records (Document, Version, Audit Log)
        """
        # 1. Validation
        allowed_extensions = {".pdf", ".docx"}
        ext = f".{file.filename.split('.')[-1].lower()}" if "." in file.filename else ""
        if ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {allowed_extensions}")
            
        # 2. Extract Text
        try:
            file_bytes = file.file.read()
            if ext == ".pdf":
                # Save temporarily for pdfplumber or read directly
                # pdfplumber prefers a file path or a bytesIO object
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(file_bytes)
                    tmp_path = tmp.name
                
                try:
                    raw_text = extract_pdf(tmp_path)
                finally:
                    import os
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
            elif ext == ".docx":
                raw_text = extract_docx(file_bytes)
                
            if not raw_text.strip():
                raise HTTPException(status_code=400, detail="Could not extract any text from the document.")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error extracting text: {str(e)}")
            
        # 3. Checksum & Duplicates
        checksum = generate_checksum(raw_text)
        existing_version = self.repo.get_version_by_checksum(checksum)
        if existing_version:
            raise HTTPException(status_code=409, detail=f"Duplicate document detected. Version {existing_version.version_number} of document {existing_version.document_id} has the exact same content.")
            
        try:    
            # Check if this should be a new document or a new version of an existing one.
            # Simplified for this flow: assume new document on every unique upload unless specified
            # A more robust system would allow uploading a new version tied to an existing document_id
            
            db_doc = self.repo.create_document(
                title=file.filename,
                department=department,
                created_by=current_user.id
            )
            
            # 4. Save to Storage
            # Need a unique string for the storage prefix. Using a fast UUID for safety before DB commit.
            import uuid
            temp_ver_id = str(uuid.uuid4())
            file_path = save_upload_file(file, temp_ver_id)
            
            # 5. Database Records
            db_version = self.repo.create_version(
                document_id=db_doc.id,
                version_number=1, # Since we assume new document here
                checksum=checksum,
                file_path=file_path,
                raw_text=raw_text,
                uploaded_by=current_user.id
            )
            
            # Update the file name to use the actual version ID if desired, or just leave it
            # For simplicity, keeping the UUID prefix strategy
            
            # Audit log
            audit_log = self.repo.log_audit(
                action_type="DOCUMENT_UPLOADED",
                user_id=current_user.id,
                document_id=db_doc.id,
                version_id=db_version.id,
                metadata={
                    "filename": file.filename,
                    "department": department,
                    "file_size": len(file_bytes)
                }
            )
            
            self.db.commit()
            self.db.refresh(db_doc)
            self.db.refresh(db_version)
            self.db.refresh(audit_log)
            
            return {
                "document_id": db_doc.id,
                "version_id": db_version.id,
                "version_number": db_version.version_number,
                "lifecycle_state": db_version.lifecycle_state,
                "audit_log_id": audit_log.id,
                "message": "Document uploaded successfully"
            }
            
        except Exception as e:
            self.db.rollback()
            if 'file_path' in locals():
                delete_stored_file(file_path)
            raise HTTPException(status_code=500, detail=f"Failed to process upload: {str(e)}")

    def approve_document(self, version_id: UUID, current_user: User):
        """
        Handles approval pipeline:
        1. Validate current state
        2. Process approval
        3. Generate structure (chunks)
        4. (Deferred) Generate embeddings
        """
        try:
            version = self.repo.get_version_by_id(version_id)
            if not version:
                raise HTTPException(status_code=404, detail="Version not found")
                
            if version.lifecycle_state not in [LifecycleState.UPLOADED, LifecycleState.UNDER_REVIEW]:
                raise HTTPException(status_code=400, detail=f"Cannot approve document in state: {version.lifecycle_state}")
                
            # 1. & 2. Update state
            version = self.repo.update_version_state(
                version_id=version_id, 
                state=LifecycleState.APPROVED,
                approved_by=current_user.id
            )
            
            # 3. Generate Chunks (section-based)
            from app.utils.file_parser import split_into_sections
            chunks_data = split_into_sections(version.raw_text)
            self.repo.create_chunks(version_id, chunks_data)
            
            # Also update chunking metadata
            version.chunking_config = {
                "strategy": "section-based",
                "max_section_words": 600,
                "chunk_count": len(chunks_data),
                "timestamp": version.approved_at.isoformat() if version.approved_at else None
            }
            
            # 4. Generate embeddings and store in pgvector
            from app.services.embedding_service import EmbeddingService
            embedding_svc = EmbeddingService(self.db)
            embedding_result = embedding_svc.embed_version(version_id)
            
            # Add Audit Log
            self.repo.log_audit(
                action_type="DOCUMENT_APPROVED",
                user_id=current_user.id,
                document_id=version.document_id,
                version_id=version.id,
                metadata={
                    "chunks_generated": len(chunks_data)
                }
            )
            
            self.db.commit()
            
            return {
                "document_id": version.document_id,
                "version_id": version.id,
                "lifecycle_state": version.lifecycle_state,
                "approved_by": version.approved_by,
                "approved_at": version.approved_at,
                "message": "Document approved and chunks generated successfully"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to approve document: {str(e)}")

    def get_document_file(self, version_id: UUID, current_user: User) -> str:
        """
        Retrieves the file path for the given document version.
        Available to any authenticated role.
        """
        version = self.repo.get_version_by_id(version_id)
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")
            
        if not version.file_path:
            raise HTTPException(status_code=404, detail="File path not found for this version.")
            
        import os
        if not os.path.exists(version.file_path):
             raise HTTPException(status_code=404, detail="Actual file not found on disk.")
             
        return version.file_path
