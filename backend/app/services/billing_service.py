import stripe
import logging
import datetime
from datetime import datetime as dt_datetime, timezone
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.domain.models import User
from backend.app.schemas.billing import BillingHistoryItem
from backend.app.services import voucher_service

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

def is_subscription_active(user: User) -> bool:
    """
    Helper to check if a user has an active premium subscription or is in dev mode.
    """
    if settings.ENABLE_DEVELOPER_MODE:
        return True
    return get_effective_plan(user) == "premium"

def get_effective_plan(user: User) -> str:
    """
    Determines the effective plan (free/premium) based on subscription status and expiration.
    Used by tests and UI to show the real current state.
    """
    now = dt_datetime.now(timezone.utc)
    
    # 1. Stripe Active
    if user.subscription_status in ["active", "trialing"]:
        return "premium"
        
    # 2. Local Voucher Active
    if user.subscription_expires_at and user.subscription_expires_at > now:
        return "premium"
        
    return "free"

async def get_unified_history(db: AsyncSession, user: User) -> List[BillingHistoryItem]:
    """
    Business logic to aggregate billing history from local vouchers and Stripe invoices.
    """
    history = []
    
    # 1. Local Voucher History
    try:
        vouchers = await voucher_service.get_user_voucher_history(db, user.id)
        for v in vouchers:
            history.append(BillingHistoryItem(
                id=f"vouch_{v.id}",
                date=v.redeemed_at or v.created_at,
                type="voucher",
                description=f"Canje de código: {v.code}",
                status="Aplicado",
                amount=f"{v.duration_days} Días"
            ))
    except Exception as e:
        logger.error(f"Error fetching local voucher history for user {user.id}: {e}")

    # 2. Stripe Invoice History
    if user.stripe_customer_id:
        try:
            invoices = stripe.Invoice.list(customer=user.stripe_customer_id, limit=10)
            for inv in invoices.data:
                amount_formatted = f"{(inv.amount_paid / 100):.2f} {inv.currency.upper()}"
                history.append(BillingHistoryItem(
                    id=f"inv_{inv.id}",
                    date=dt_datetime.fromtimestamp(inv.created, tz=timezone.utc),
                    type="payment",
                    description=inv.lines.data[0].description if inv.lines.data else "Suscripción AjaxSecurFlow",
                    amount=amount_formatted,
                    status="Pagado" if inv.paid else "Pendiente",
                    download_url=inv.invoice_pdf
                ))
        except Exception as e:
            logger.error(f"Error fetching Stripe invoices for user {user.id}: {e}")

    # 3. Sort by date desc
    history.sort(key=lambda x: x.date, reverse=True)
    return history
