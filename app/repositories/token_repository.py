import uuid
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import update
from app.models.refresh_token import RefreshToken

class TokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_refresh_token(self, user_id: str | uuid.UUID, token_hash: str, expires_at: datetime) -> RefreshToken:
        if isinstance(user_id, str):
            user_id = str(user_id)
        db_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        self.db.add(db_token)
        self.db.commit()
        self.db.refresh(db_token)
        return db_token

    def get_valid_refresh_token(self, token_hash: str) -> Optional[RefreshToken]:
        # Consider a token valid if it matches the hash and is not revoked
        return self.db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked == False
        ).first()

    def revoke_refresh_token(self, token_hash: str) -> None:
        self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .values(revoked=True)
        )
        self.db.commit()

    def revoke_all_user_tokens(self, user_id: str | uuid.UUID) -> None:
        if isinstance(user_id, str):
            user_id = str(user_id)
        self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .values(revoked=True)
        )
        self.db.commit()
