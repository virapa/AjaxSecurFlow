from datetime import datetime as dt_datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from backend.app.shared.infrastructure.database.models import Base

class AuditLog(Base):
    """
    Immutable log of core system actions for security auditing.
    """
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True, nullable=True)
    endpoint: Mapped[str] = mapped_column(String, nullable=False)
    method: Mapped[str] = mapped_column(String, nullable=True)
    action: Mapped[str] = mapped_column(String, nullable=False)
    payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # New Security Context Fields
    ip_address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    severity: Mapped[str] = mapped_column(String, default="INFO", index=True) # INFO, WARNING, CRITICAL
    resource_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True) # E.g., hub_id
    
    # performance & tracking
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    correlation_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    
    timestamp: Mapped[dt_datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
