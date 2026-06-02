# create_tables.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base

# Import all models so SQLAlchemy can detect them
from app.models.user import User
from app.models.document import (
    Document,
    DocumentVersion,
    Chunk,
    AuditLog,
    QueryAuditLog
)
from app.models.refresh_token import RefreshToken


DATABASE_URL = "sqlite:///./app.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Create all tables
Base.metadata.create_all(bind=engine)

print("Database tables created successfully!")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
