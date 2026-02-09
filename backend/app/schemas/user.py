from pydantic import BaseModel, EmailStr, ConfigDict, Field
import datetime
from datetime import datetime as dt_datetime
from typing import Optional
from enum import Enum
from backend.app.schemas.ajax import AjaxUserInfo

class SubscriptionPlan(str, Enum):
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    PREMIUM = "premium"

class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="User's primary email address")
    password: str = Field(..., description="User password (will be hashed before storage)")

class UserRead(BaseModel):
    id: int = Field(..., description="Unique internal database ID for the user")
    email: EmailStr = Field(..., description="User's primary email address")
    is_active: bool = Field(True, description="Whether the user account is active")
    subscription_plan: SubscriptionPlan = Field(SubscriptionPlan.FREE, description="Plan identifier")
    subscription_active: bool = Field(False, description="True if the plan is currently valid and paid")
    subscription_expires_at: Optional[dt_datetime] = Field(None, description="When the current plan expires")
    billing_status: Optional[str] = Field(None, description="Technical status (active, trialing, past_due, inactive)")
    ajax_info: Optional[AjaxUserInfo] = None
    
    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None
    subscription_plan: Optional[SubscriptionPlan] = None
