import hashlib
from datetime import datetime
import datetime as dt_module
from datetime import timezone
from typing import Optional
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session
import uuid

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token
from app.core.hashing import verify_pwd, hash_pwd
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.repositories.token_repository import TokenRepository
from app.core.database import get_db

security = HTTPBearer()

ALLOWED_DOMAINS = ["company.com", "intertalks.com"] # Whitelist domains as required

class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.token_repo = TokenRepository(db)

    def hash_token(self, token: str) -> str:
        # Generate sha256 hash formatting for refresh token DB storage
        return hashlib.sha256(token.encode()).hexdigest()

    def register(self, email: str, password: str, full_name: Optional[str] = None):
        domain = email.split("@")[-1] if "@" in email else ""
        if domain not in ALLOWED_DOMAINS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Non-company email domains are rejected."
            )
        
        existing_user = self.user_repo.get_user_by_email(email)
        if existing_user:
            # We don't want to leak if an email exists directly at login, but for registration 
            # we can either pretend it works or reject. For strictness, usually 400 is fine here.
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email domain invalid or user already exists."
            )
            
        hashed_password = hash_pwd(password)
        # Force default role viewer, is_active=True handled in repo
        user = self.user_repo.create_user(
            email=email, 
            full_name=full_name, 
            hashed_password=hashed_password, 
            role=UserRole.VIEWER
        )
        return user

    def login(self, email: str, password: str):
        # 1. Reject inactive users, User exists, Verify password

        user = self.user_repo.get_user_by_email(email)
        
        
        # Don't leak whether email exists -> unifying error message
        auth_error = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email hai or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        if not user:
            raise auth_error
            
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
            
        if not verify_pwd(password, user.hashed_password):
            print("Invalid password")
            raise auth_error
            
        # 2. Issue Access + Refresh token
        access_token = create_access_token(subject=str(user.id), role=user.role.value)
        refresh_token_plain = create_refresh_token(subject=str(user.id))
        
        # 3. Revoke any old refresh tokens, then store new hashed refresh token
        self.token_repo.revoke_all_user_tokens(user.id)
        expires_at = datetime.now(timezone.utc) + dt_module.timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        self.token_repo.create_refresh_token(
            user_id=user.id,
            token_hash=self.hash_token(refresh_token_plain),
            expires_at=expires_at
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token_plain,
            "token_type": "bearer"
        }

    def rotate_refresh_token(self, refresh_token: str):
        try:
            payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
            
        token_hash = self.hash_token(refresh_token)
        db_token = self.token_repo.get_valid_refresh_token(token_hash)
        
        if not db_token or db_token.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked or expired")
            
        # Revoke old token
        self.token_repo.revoke_refresh_token(token_hash)
        
        # Issue new tokens
        user = self.user_repo.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive or deleted")
            
        new_access_token = create_access_token(subject=str(user.id), role=user.role.value)
        new_refresh_token = create_refresh_token(subject=str(user.id))
        
        expires_at = datetime.now(timezone.utc) + dt_module.timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        self.token_repo.create_refresh_token(
            user_id=user.id,
            token_hash=self.hash_token(new_refresh_token),
            expires_at=expires_at
        )
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }

    def logout(self, refresh_token: str):
        token_hash = self.hash_token(refresh_token)
        self.token_repo.revoke_refresh_token(token_hash)


# --- Dependency Injection for Auth Enforcement ---

def get_current_user(db: Session = Depends(get_db), token: HTTPAuthorizationCredentials = Depends(security)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user_repo = UserRepository(db)
    user = user_repo.get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return user

def require_role(required_role: UserRole):
    """
    Enforces authorization rules relying directly on users.role column
    """
    def role_checker(current_user: User = Depends(get_current_user)):
        roles_hierarchy = {
            UserRole.VIEWER: 1,
            UserRole.CONTRIBUTOR: 2,
            UserRole.REVIEWER: 3,
            UserRole.ADMIN: 4
        }
        
        if roles_hierarchy.get(current_user.role, 0) < roles_hierarchy.get(required_role, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Requires {required_role.value} role."
            )
        return current_user
    return role_checker
