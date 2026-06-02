
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.document import LifecycleState

class DocumentVersionOut(BaseModel):
    id: str
    document_id: str
    version_number: int
    lifecycle_state: LifecycleState
    uploaded_by: str
    uploaded_at: datetime
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    checksum: str
    
    model_config = ConfigDict(from_attributes=True)

class DocumentOut(BaseModel):
    id: str
    title: str
    department: str
    created_by: str
    created_at: datetime
    versions: List[DocumentVersionOut] = []
    
    model_config = ConfigDict(from_attributes=True)

class DocumentUploadResponse(BaseModel):
    document_id: str
    version_id: str
    version_number: int
    lifecycle_state: LifecycleState
    audit_log_id: str
    message: str

class DocumentApproveResponse(BaseModel):
    document_id: str
    version_id: str
    lifecycle_state: LifecycleState
    approved_by: str
    approved_at: datetime
    message: str
