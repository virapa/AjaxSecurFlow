from datetime import datetime as dt_datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from backend.app.shared.infrastructure.database.models import Base

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
    subscription_expires_at: Mapped[Optional[dt_datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[dt_datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[dt_datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())


class ApiToken(Base):
    """
    Long-lived integration token (e.g. Home Assistant).
    Only the SHA-256 hash is stored; the raw token is shown once at creation.
    """
    __tablename__ = "api_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    prefix: Mapped[str] = mapped_column(String(12), nullable=False)
    last_used_at: Mapped[Optional[dt_datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[dt_datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[Optional[dt_datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[dt_datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def is_active(self, now: dt_datetime) -> bool:
        if self.revoked_at is not None:
            return False
        if self.expires_at is not None and self.expires_at <= now:
            return False
        return True

    def __repr__(self):
        return f"<ApiToken(id={self.id}, user={self.user_id}, prefix={self.prefix})>"
