from datetime import datetime as dt_datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from backend.app.shared.infrastructure.database.models import Base

class ProcessedStripeEvent(Base):
    """
    Tracking of processed Stripe events to ensure idempotency.
    """
    __tablename__ = "processed_stripe_events"
    
    id: Mapped[str] = mapped_column(String, primary_key=True) # Stripe Event ID
    event_type: Mapped[str] = mapped_column(String, index=True)
    processed_at: Mapped[dt_datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Voucher(Base):
    """
    Activation codes for service subscription (B2B/Offline sales).
    """
    __tablename__ = "vouchers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    plan: Mapped[str] = mapped_column(String, nullable=False, default="premium")
    
    is_redeemed: Mapped[bool] = mapped_column(Boolean, default=False)
    redeemed_by_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    redeemed_at: Mapped[Optional[dt_datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_at: Mapped[dt_datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
