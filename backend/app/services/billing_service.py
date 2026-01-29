import stripe
from datetime import datetime, timezone
from backend.app.core.config import settings
from backend.app.domain.models import User

if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY.get_secret_value()

def get_effective_plan(user: User) -> str:
    """
    Determines the current active plan for a user considering expiration and Stripe status.
    If the premium time (voucher or stripe) has ended, returns 'free'.

    Args:
        user: The user object from database.

    Returns:
        str: 'premium' or 'free'.
    """
    # 1. Check for recurring active subscription (highest priority)
    if user.subscription_status in ["active", "trialing"]:
        return "premium"

    # 2. Check for Voucher expiration
    if user.subscription_expires_at:
        if user.subscription_expires_at > datetime.now(timezone.utc):
            return "premium"

    # 3. Default to free
    return "free"

async def get_user_subscription_status(user: User) -> str:
    """
    Check current user's subscription status.
    
    In a real app, we might want to sync this via webhooks.
    In the future, this service will handle Stripe API calls for sync.

    Args:
        user: The user object from database.

    Returns:
        str: Current status (active, trial, past_due, inactive).
    """
    # For now, we trust the DB field. 
    return user.subscription_status or "inactive"

def is_subscription_active(user: User) -> bool:
    """
    Business logic to determine if a user can access the Proxy.

    Args:
        user: The user object from database.

    Returns:
        bool: True if user has active/premium access.
    """
    # 1. Developer Mode: Bypass subscription check
    if settings.ENABLE_DEVELOPER_MODE:
        return True

    return get_effective_plan(user) == "premium"
