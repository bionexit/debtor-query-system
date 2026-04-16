from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    OPERATOR = "OPERATOR"
    VIEWER = "VIEWER"


class UserStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    LOCKED = "LOCKED"


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    full_name: Optional[str] = Field(None, max_length=100)
    role: UserRole = UserRole.VIEWER

    @field_validator('role', mode='before')
    @classmethod
    def role_uppercase(cls, v):
        if isinstance(v, str):
            return v.upper()
        return v


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)
    created_by_id: Optional[int] = None

    @field_validator('role', mode='before')
    @classmethod
    def role_uppercase(cls, v):
        if isinstance(v, str):
            return v.upper()
        return v


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    full_name: Optional[str] = Field(None, max_length=100)
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None


class UserPasswordUpdate(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6, max_length=100)


class UserResponse(UserBase):
    id: int
    status: UserStatus
    is_superadmin: bool
    login_attempts: int
    locked_until: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime]
    created_by_id: Optional[int]

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str
    captcha_key: Optional[str] = None
    captcha_value: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class H5TokenRequest(BaseModel):
    phone: str
    sms_code: str


class H5TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    expires_days: int


class PasswordResetRequest(BaseModel):
    phone: str
    sms_code: str
    new_password: str = Field(..., min_length=6, max_length=100)


class PasswordResetByAdminRequest(BaseModel):
    user_id: int
    new_password: str = Field(..., min_length=6, max_length=100)
