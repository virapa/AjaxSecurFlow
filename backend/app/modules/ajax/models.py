from datetime import datetime as dt_datetime
from typing import Optional, Any
from sqlalchemy import String, DateTime, JSON, ForeignKey, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from backend.app.shared.infrastructure.database.models import Base

class AjaxSQSEvent(Base):
    """
    Audit log for raw events received from Ajax Systems via Amazon SQS.
    Follows OWASP 2025 recommendations for centralized auditing.
    """
    __tablename__ = "ajax_sqs_events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    message_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String, index=True, nullable=False)
    hub_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    # Ajax's own event identifier. A single Ajax event is fanned out as one
    # SQS message per recipient user, so several distinct SQS messages can
    # share the same ajax_event_id: used to deduplicate notifications.
    ajax_event_id: Mapped[Optional[str]] = mapped_column(String, index=True, nullable=True)

    # Raw JSON payload for deep auditing and future re-processing
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    # Metadata
    received_at: Mapped[dt_datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    processed_at: Mapped[Optional[dt_datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<AjaxSQSEvent(id={self.id}, type={self.event_type}, hub={self.hub_id})>"

class AjaxHubState(Base):
    """
    Last known state per hub, updated with every event received via SQS.
    Acts as the source of truth for the "last event / last state" of a hub.
    """
    __tablename__ = "ajax_hub_states"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    hub_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)

    last_event_type: Mapped[str] = mapped_column(String, nullable=False)
    last_message_id: Mapped[str] = mapped_column(String, nullable=False)
    last_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    updated_at: Mapped[dt_datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self):
        return f"<AjaxHubState(hub={self.hub_id}, last_event={self.last_event_type})>"

class UserHub(Base):
    """
    Mapping between internal users and Ajax hubs.
    Used for filtering SQS events and optimizing lookups.
    """
    __tablename__ = "user_hubs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    hub_id: Mapped[str] = mapped_column(String, index=True, nullable=False)

    # Cache some basic info to avoid API calls during SQS processing
    hub_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    created_at: Mapped[dt_datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<UserHub(user_id={self.user_id}, hub_id={self.hub_id})>"

class UserWebhook(Base):
    """
    User configured webhooks for dispatching real-time hub events to external systems (e.g. Home Assistant).
    """
    __tablename__ = "user_webhooks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    hub_id: Mapped[Optional[str]] = mapped_column(String, index=True, nullable=True) # None = all hubs of this user
    target_url: Mapped[str] = mapped_column(String, nullable=False)
    secret_token: Mapped[Optional[str]] = mapped_column(String, nullable=True) # Used for HMAC-SHA256 signature
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[dt_datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<UserWebhook(id={self.id}, user_id={self.user_id}, target_url={self.target_url})>"
