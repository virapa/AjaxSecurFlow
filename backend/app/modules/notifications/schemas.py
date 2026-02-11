from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime as dt_datetime
from typing import Optional, List

class NotificationBase(BaseModel):
    title: str = Field(..., description="Short summary of the alert")
    message: str = Field(..., description="Detailed explanation")
    type: str = Field("info", description="Alert severity: info, warning, success, error")
    link: Optional[str] = Field(None, description="Optional relative or absolute link for action")

class NotificationRead(NotificationBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="Unique DB ID")
    is_read: bool = Field(..., description="Read status")
    created_at: dt_datetime = Field(..., description="Alert timestamp")

class NotificationSummary(BaseModel):
    unread_count: int = Field(..., description="Total unread alerts for this user")
    notifications: List[NotificationRead] = Field(..., description="Recent notification objects")
