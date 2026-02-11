from datetime import datetime as dt_datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from backend.app.shared.infrastructure.database.models import Base

class Notification(Base):
    """
    In-app notifications for end-users regarding account or system events.
    """
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    
    title: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, default="info") # info, warning, error, success
    link: Mapped[Optional[str]] = mapped_column(String, nullable=True) # Optional URL to click
    
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[dt_datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
