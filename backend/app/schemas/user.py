from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr = Field(..., description="User's primary email address (must be unique)")
    is_active: bool = Field(True, description="Whether the user account is currently active")
    subscription_status: Optional[str] = Field(None, description="Current Stripe subscription status (e.g., 'active', 'past_due')")
    subscription_plan: str = Field("free", description="Subscribed plan identifier (e.g., 'basic', 'premium')")

class UserCreate(UserBase):
    password: str = Field(..., description="User password (will be hashed before storage)")

class UserRead(UserBase):
    id: int = Field(..., description="Unique internal database ID for the user")
    
    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None
