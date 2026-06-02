import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    ForeignKey
)

from sqlalchemy.orm import relationship

from app.models.base import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    user_id = Column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    token_hash = Column(
        String,
        nullable=False
    )

    expires_at = Column(
        DateTime,
        nullable=False
    )

    revoked = Column(
        Boolean,
        default=False
    )

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    user = relationship(
        "User",
        backref="refresh_tokens"
    )