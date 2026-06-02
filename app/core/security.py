from datetime import datetime, timedelta, timezone
from typing import Any, Union
from jose import jwt

from app.core.config import settings

def create_access_token(
    subject: Union[str, Any], role: str, expires_delta: timedelta = None
) -> str:
    """
    Create access token with payload matching requirement:
    { "sub": "<user_id>", "role": "ADMIN", "exp": <timestamp> }
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject), "role": role}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    """
    Create refresh token. Refresh token must NOT contain sensitive claims.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
