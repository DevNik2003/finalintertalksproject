from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import require_role
from app.models.user import User, UserRole
from app.schemas.auth import UserOut
from app.repositories.user_repository import UserRepository

router = APIRouter()

class UserUpdateRequest(BaseModel):
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

@router.get("/users", response_model=List[UserOut])
def get_all_users(
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_role(UserRole.ADMIN))
):
    """
    List all users.
    Only accessible by ADMIN.
    """
    repo = UserRepository(db)
    return repo.get_all_users()

@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: str,
    payload: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_role(UserRole.ADMIN))
):
    """
    Update a user's role and/or is_active status.
    Only accessible by ADMIN.
    Admin cannot modify own role or deactivate self.
    """
    # Prevent self-modification
    if str(current_admin.id) == str(user_id):
        if payload.role is not None:
            raise HTTPException(status_code=400, detail="Cannot modify your own role")
        if payload.is_active is not None and not payload.is_active:
            raise HTTPException(status_code=400, detail="Cannot deactivate yourself")

    repo = UserRepository(db)
    updated_user = repo.update_user(user_id, role=payload.role, is_active=payload.is_active)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user
