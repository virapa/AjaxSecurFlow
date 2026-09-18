from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator
from typing import Optional
from enum import Enum
from datetime import datetime as dt_datetime
from backend.app.modules.ajax.schemas import AjaxUserInfo

# Shared Enums/Models if any
class SubscriptionPlan(str, Enum):
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    PREMIUM = "premium"

# Auth Schemas
class LoginRequest(BaseModel):
    username: str = Field(..., description="Your Ajax Email")
    password: str = Field(..., description="Your Ajax Password")

class Token(BaseModel):
    access_token: str = Field(..., description="JWT access token for API requests (short-lived)")
    refresh_token: str = Field(..., description="JWT refresh token to obtain new access tokens (long-lived)")
    token_type: str = Field("bearer", description="Token type, always 'bearer'")
    userId: Optional[str] = Field(None, description="Ajax hex User ID")

class TokenData(BaseModel):
    email: Optional[str] = None

class TokenRefreshRequest(BaseModel):
    refresh_token: str = Field(..., description="The long-lived refresh token received during login")

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    userId: Optional[str] = None

# User Schemas
class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="User's primary email address")
    password: str = Field(..., description="User password (will be hashed before storage)")

class UserRead(BaseModel):
    id: int = Field(..., description="Unique internal database ID for the user")
    email: EmailStr = Field(..., description="User's primary email address")
    is_active: bool = Field(True, description="Whether the user account is active")
    subscription_plan: str = Field(..., description="Plan identifier") # Using str for flexibility
    subscription_status: Optional[str] = Field(None, description="Technical status (active, trialing, past_due, inactive)")
    subscription_expires_at: Optional[dt_datetime] = Field(None, description="When the current plan expires")
    
    model_config = ConfigDict(from_attributes=True)

class UserReadMe(UserRead):
    subscription_active: bool
    billing_status: str
    ajax_info: Optional[AjaxUserInfo] = None

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None
    
class ErrorMessage(BaseModel):
    detail: str = Field(..., description="Details regarding the error")

# Integration (API) Tokens
class ApiTokenCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64, description="Label for this token, e.g. 'Home Assistant'")
    expires_in_days: Optional[int] = Field(None, ge=1, le=3650, description="Optional expiry in days. Null = never expires")

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, v):
        return v.strip() if isinstance(v, str) else v

class ApiTokenRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    prefix: str = Field(..., description="First 12 characters, to identify the token in the UI")
    last_used_at: Optional[dt_datetime] = None
    expires_at: Optional[dt_datetime] = None
    created_at: dt_datetime

class ApiTokenCreated(ApiTokenRead):
    token: str = Field(..., description="Raw token. Shown only once at creation")
