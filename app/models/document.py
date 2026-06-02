import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    Float,
    Date,
    Boolean,
    DateTime,
    ForeignKey,
    Enum,
    JSON
)

from sqlalchemy.orm import relationship

from app.models.base import Base


# =========================================================
# ENUMS
# =========================================================

class LifecycleState(str, enum.Enum):
    UPLOADED = "UPLOADED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    DEPRECATED = "DEPRECATED"


# =========================================================
# DOCUMENT
# =========================================================

class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    title = Column(Text, nullable=False)
    department = Column(Text, nullable=False)

    created_by = Column(
        String,
        ForeignKey("users.id"),
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    versions = relationship(
        "DocumentVersion",
        back_populates="document",
        cascade="all, delete-orphan"
    )

    creator = relationship(
        "User",
        foreign_keys=[created_by]
    )


# =========================================================
# DOCUMENT VERSION
# =========================================================

class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    document_id = Column(
        String,
        ForeignKey("documents.id", ondelete="RESTRICT"),
        nullable=False
    )

    version_number = Column(Integer, nullable=False)

    checksum = Column(
        Text,
        nullable=False,
        unique=True
    )

    lifecycle_state = Column(
        Enum(LifecycleState),
        default=LifecycleState.UPLOADED
    )

    effective_date = Column(Date, nullable=True)

    uploaded_by = Column(
        String,
        ForeignKey("users.id"),
        nullable=False
    )

    uploaded_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    approved_by = Column(
        String,
        ForeignKey("users.id"),
        nullable=True
    )

    approved_at = Column(
        DateTime,
        nullable=True
    )

    raw_text = Column(
        Text,
        nullable=False,
        default=""
    )

    chunking_config = Column(JSON, nullable=True)

    embedding_metadata = Column(JSON, nullable=True)

    file_path = Column(Text, nullable=True)

    document = relationship(
        "Document",
        back_populates="versions"
    )

    chunks = relationship(
        "Chunk",
        back_populates="version",
        cascade="all, delete-orphan"
    )

    uploader = relationship(
        "User",
        foreign_keys=[uploaded_by]
    )

    approver = relationship(
        "User",
        foreign_keys=[approved_by]
    )


# =========================================================
# CHUNK
# =========================================================

class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    version_id = Column(
        String,
        ForeignKey("document_versions.id", ondelete="CASCADE"),
        nullable=False
    )

    chunk_index = Column(Integer, nullable=False)

    content = Column(Text, nullable=False)

    section_title = Column(Text, nullable=True)

    section_number = Column(Text, nullable=True)

    token_count = Column(Integer, nullable=True)

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    version = relationship(
        "DocumentVersion",
        back_populates="chunks"
    )


# =========================================================
# AUDIT LOG
# =========================================================

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    action_type = Column(Text, nullable=False)

    user_id = Column(
        String,
        ForeignKey("users.id"),
        nullable=False
    )

    document_id = Column(
        String,
        ForeignKey("documents.id"),
        nullable=False
    )

    version_id = Column(
        String,
        ForeignKey("document_versions.id"),
        nullable=False
    )

    timestamp = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    extra_info = Column(JSON, nullable=True)

    user = relationship(
        "User",
        foreign_keys=[user_id]
    )

    document = relationship(
        "Document",
        foreign_keys=[document_id]
    )

    version = relationship(
        "DocumentVersion",
        foreign_keys=[version_id]
    )


# =========================================================
# QUERY AUDIT LOG
# =========================================================

class QueryAuditLog(Base):
    __tablename__ = "query_audit_logs"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    user_id = Column(
        String,
        ForeignKey("users.id"),
        nullable=False
    )

    query_text = Column(Text, nullable=False)

    top_similarity = Column(Float, nullable=True)

    result_status = Column(
        Text,
        nullable=False
    )

    extra_metadata = Column(
        "metadata",
        JSON,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    user = relationship(
        "User",
        foreign_keys=[user_id]
    )