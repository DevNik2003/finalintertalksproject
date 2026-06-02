from pydantic import BaseModel, EmailStr
from app.models.user import UserRole
import uuid

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None

class UserOut(BaseModel):
    id: str
    email: str
    full_name: str | None
    role: UserRole
    is_active: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str
