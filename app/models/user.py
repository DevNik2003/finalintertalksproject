import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    String,
    Boolean,
    Enum,
    DateTime
)

from app.models.base import Base


class UserRole(str, enum.Enum):
    VIEWER = "VIEWER"
    CONTRIBUTOR = "CONTRIBUTOR"
    REVIEWER = "REVIEWER"
    ADMIN = "ADMIN"


class User(Base):
    __tablename__ = "users"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    email = Column(
        String,
        unique=True,
        nullable=False
    )

    full_name = Column(
        String,
        nullable=False
    )

    role = Column(
        Enum(UserRole),
        nullable=False
    )

    is_active = Column(
        Boolean,
        default=True
    )

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    hashed_password = Column(
        String,
        nullable=False
    )