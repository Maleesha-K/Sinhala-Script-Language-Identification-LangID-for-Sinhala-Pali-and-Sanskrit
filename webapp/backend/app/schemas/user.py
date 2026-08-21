import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from app.db.models.user import UserRole

class UserBase(BaseModel):
    email: EmailStr
    display_name: str | None = Field(default=None, max_length=128)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=128)
    password: str | None = Field(default=None, min_length=8)

class UserResponse(UserBase):
    id: uuid.UUID
    role: UserRole
    is_active: bool
    storage_used_bytes: int
    credits_balance: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
