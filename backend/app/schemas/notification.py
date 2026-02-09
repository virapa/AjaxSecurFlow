from pydantic import BaseModel, ConfigDict
import datetime
from typing import Optional, List

class NotificationBase(BaseModel):
    title: str
    message: str
    type: str = "info"
    link: Optional[str] = None

class NotificationRead(NotificationBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_read: bool
    created_at: datetime.datetime

class NotificationSummary(BaseModel):
    unread_count: int
    notifications: List[NotificationRead]
