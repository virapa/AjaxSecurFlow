from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional
from enum import Enum
from backend.app.schemas.ajax import AjaxUserInfo

class SubscriptionPlan(str, Enum):
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    PREMIUM = "premium"

class UserBase(BaseModel):
    email: EmailStr = Field(..., description="User's primary email address (must be unique)")
    is_active: bool = Field(True, description="Whether the user account is currently active")
    subscription_status: Optional[str] = Field(None, description="Current Stripe subscription status (e.g., 'active', 'past_due')")
    subscription_plan: SubscriptionPlan = Field(SubscriptionPlan.FREE, description="Subscribed plan identifier")

class UserCreate(UserBase):
    password: str = Field(..., description="User password (will be hashed before storage)")

class UserRead(UserBase):
    id: int = Field(..., description="Unique internal database ID for the user")
    ajax_info: Optional[AjaxUserInfo] = None
    
    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None
