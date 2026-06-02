from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db)
) -> User:
    """Gets the current user from the access token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    return user

def require_role(*allowed_roles: UserRole):
    """
    Dependency generator for role-based access control.
    Verifies that the current user has one of the allowed roles.
    Includes ADMIN automatically for broad access unless restricted.
    """
    def verify_role(current_user: User = Depends(get_current_user)):
        roles_to_check = list(allowed_roles)
        # ADMIN is implicitly allowed for everything unless it's strictly another role
        if UserRole.ADMIN not in roles_to_check:
            roles_to_check.append(UserRole.ADMIN)
            
        if current_user.role not in roles_to_check:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required roles: {[r.value for r in allowed_roles]}"
            )
        return current_user
        
    return verify_role
