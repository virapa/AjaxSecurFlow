from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, Integer, DateTime, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func

# Clean Architecture: Domain components should have 0 external dependencies besides standard lib and ORM/Data definitions.
# We are using SQLAlchemy as our data mapper.

class Base(DeclarativeBase):
    pass

class User(Base):
    """
    Represents a registered user in the SaaS platform.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    
    # Stripe integration for SaaS monetization
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True, index=True)
    subscription_id: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    subscription_status: Mapped[Optional[str]] = mapped_column(String, nullable=True) # active, past_due, etc.
    subscription_plan: Mapped[str] = mapped_column(String, default="free")
    subscription_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

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
    
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class ProcessedStripeEvent(Base):
    __tablename__ = "processed_stripe_events"
    
    id: Mapped[str] = mapped_column(String, primary_key=True) # Stripe Event ID
    event_type: Mapped[str] = mapped_column(String, index=True)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Voucher(Base):
    """
    Activation codes for service subscription (B2B/Offline sales).
    """
    __tablename__ = "vouchers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    
    is_redeemed: Mapped[bool] = mapped_column(Boolean, default=False)
    redeemed_by_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    redeemed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
