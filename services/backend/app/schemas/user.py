from pydantic import BaseModel, EmailStr
from datetime import datetime
from uuid import UUID
from app.models.user import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    role: UserRole = UserRole.viewer


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    username: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None


class UserOut(BaseModel):
    id: UUID
    email: str
    username: str
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login: datetime | None

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    refresh_token: str
