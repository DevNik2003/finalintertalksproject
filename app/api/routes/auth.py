from typing import Any, Optional
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.hashing import verify_pwd, hash_pwd
from app.core.config import settings
from app.services.auth_service import AuthService, get_current_user, require_role
from app.models.user import User, UserRole
from app.schemas.auth import UserCreate, UserOut, Token

router = APIRouter()

# --- Rate Limiting & HTTPS Dependency Stubs ---
def rate_limit(request: Request):
    pass

def https_only(request: Request):
    if request.url.scheme != 'https' and not request.url.hostname in ['localhost', '127.0.0.1']:
        raise HTTPException(status_code=400, detail="HTTPS required")

# --- Cookie Config ---
COOKIE_KEY = "refresh_token"
COOKIE_MAX_AGE = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60  # days -> seconds

def _set_refresh_cookie(response: Response, refresh_token: str):
    """Set refresh token as httpOnly cookie"""
    response.set_cookie(
        key=COOKIE_KEY,
        value=refresh_token,
        httponly=True,
        secure=False,       # Set True in production (HTTPS)
        samesite="lax",
        max_age=COOKIE_MAX_AGE,
        path="/api/v1/auth",  # Only sent on auth routes
    )

def _clear_refresh_cookie(response: Response):
    """Delete the refresh token cookie"""
    response.delete_cookie(
        key=COOKIE_KEY,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/api/v1/auth",
    )

# --- Endpoints ---

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_user(
    user_in: UserCreate, 
    db: Session = Depends(get_db), 
    _ = Depends(https_only)
) -> Any:
    """
    Register a new user. Only allows whitelist company domains.
    Assigns VIEWER role by default.
    """
    auth_service = AuthService(db)
    return auth_service.register(
        email=user_in.email, 
        password=user_in.password, 
        full_name=user_in.full_name
    )

@router.post("/login")
def login_access_token(
    response: Response,
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
    _rate_limit = Depends(rate_limit),
    _https = Depends(https_only)
) -> Any:
    """
    Login: returns access_token in body, sets refresh_token as httpOnly cookie.
    """
    auth_service = AuthService(db)
    tokens = auth_service.login(email=form_data.username, password=form_data.password)
    
    # Set refresh token as httpOnly cookie
    _set_refresh_cookie(response, tokens["refresh_token"])
    
    # Return only the access token in the response body
    return {
        "access_token": tokens["access_token"],
        "token_type": tokens["token_type"],
    }

@router.post("/refresh")
def refresh_token(
    response: Response,
    db: Session = Depends(get_db),
    refresh_token: Optional[str] = Cookie(None, alias=COOKIE_KEY),
) -> Any:
    """
    Rotate refresh token (read from httpOnly cookie) and issue new access token.
    Sets new refresh token cookie.
    """
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token cookie found")
    
    auth_service = AuthService(db)
    tokens = auth_service.rotate_refresh_token(refresh_token)
    
    # Set new refresh token cookie
    _set_refresh_cookie(response, tokens["refresh_token"])
    
    return {
        "access_token": tokens["access_token"],
        "token_type": tokens["token_type"],
    }

@router.post("/logout")
def logout(
    response: Response,
    db: Session = Depends(get_db),
    refresh_token: Optional[str] = Cookie(None, alias=COOKIE_KEY),
    _ = Depends(https_only)
) -> Any:
    """
    Revoke the refresh token and clear the cookie.
    """
    if refresh_token:
        auth_service = AuthService(db)
        auth_service.logout(refresh_token)
    
    _clear_refresh_cookie(response)
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserOut)
def read_current_user(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get current user information based on Authorization token.
    """
    return current_user

@router.post("/create-admin", response_model=UserOut)
def create_admin(
    user_in: UserCreate,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(User.email == user_in.email).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User already exists"
        )

    hashed_password = hash_pwd(user_in.password)

    admin_user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=hashed_password,
        role="CONTRIBUTOR",
        is_active=True
    )

    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)

    return admin_user