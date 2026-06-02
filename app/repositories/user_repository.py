import uuid
from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User, UserRole

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_user_by_id(self, user_id: str | uuid.UUID) -> Optional[User]:
        if isinstance(user_id, str):
            try:
                user_id = str(user_id)
            except ValueError:
                return None
        return self.db.query(User).filter(User.id == user_id).first()

    def create_user(self, email: str, hashed_password: str, full_name: str = None, role: UserRole = UserRole.VIEWER) -> User:
        db_user = User(
            email=email,
            full_name=full_name,
            hashed_password=hashed_password,
            role=role,
            is_active=True
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def get_all_users(self) -> list[User]:
        return self.db.query(User).all()

    def update_user_role(self, user_id: str | uuid.UUID, new_role: UserRole) -> Optional[User]:
        user = self.get_user_by_id(user_id)
        if user:
            user.role = new_role
            self.db.commit()
            self.db.refresh(user)
        return user

    def update_user(self, user_id: str | uuid.UUID, role: Optional[UserRole] = None, is_active: Optional[bool] = None) -> Optional[User]:
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        if role is not None:
            user.role = role
        if is_active is not None:
            user.is_active = is_active
        self.db.commit()
        self.db.refresh(user)
        return user
