import stripe
from typing import Optional
from backend.app.core.config import settings
from backend.app.domain.models import User

if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY.get_secret_value()

async def get_user_subscription_status(user: User) -> str:
    """
    Check current user's subscription status.
    In a real app, we might want to sync this via webhooks.
    """
    # For now, we trust the DB field. 
    # In the future, this service will handle Stripe API calls for sync.
    return user.subscription_status or "inactive"

from datetime import datetime, timezone

def is_subscription_active(user: User) -> bool:
    """
    Business logic to determine if a user can access the Proxy.
    """
    # 1. Developer Mode: Bypass subscription check
    if settings.ENABLE_DEVELOPER_MODE:
        return True

    # 2. Check for Voucher/Manual expiration date
    if user.subscription_expires_at:
        if user.subscription_expires_at > datetime.now(timezone.utc):
            return True

    # 3. Production: Allow active and trialing subscriptions (Stripe)
    return user.subscription_status in ["active", "trialing"]
