import stripe
import logging
import secrets
import string
from datetime import datetime as dt_datetime, timezone, timedelta
from typing import List, Optional
from sqlalchemy import select, update, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.modules.auth.models import User
from backend.app.modules.billing.models import Voucher, ProcessedStripeEvent
from backend.app.modules.billing.schemas import BillingHistoryItem

logger = logging.getLogger(__name__)

# --- Subscription Logic ---

def is_subscription_active(user: User) -> bool:
    if settings.ENABLE_DEVELOPER_MODE:
        return True
    return get_effective_plan(user) != "free"

def get_effective_plan(user: User) -> str:
    now = dt_datetime.now(timezone.utc)
    if user.subscription_status in ["active", "trialing"]:
        return user.subscription_plan
    if user.subscription_expires_at and user.subscription_expires_at > now:
        return "premium"
    return "free"

def get_plan_from_price_id(price_id: str) -> str:
    if price_id == settings.STRIPE_PRICE_ID_BASIC:
        return "basic"
    if price_id == settings.STRIPE_PRICE_ID_PRO:
        return "pro"
    if price_id == settings.STRIPE_PRICE_ID_PREMIUM:
        return "premium"
    return "free"

def can_access_feature(user: User, feature: str) -> bool:
    if settings.ENABLE_DEVELOPER_MODE:
        return True
    plan = get_effective_plan(user)
    permissions = {
        "free": [],
        "basic": ["list_hubs", "read_telemetry", "read_logs"],
        "pro": ["list_hubs", "read_telemetry", "read_logs", "send_commands"],
        "premium": ["list_hubs", "read_telemetry", "read_logs", "send_commands", "access_proxy"]
    }
    allowed = permissions.get(plan, [])
    return feature in allowed

# --- Voucher Logic ---

def generate_random_code() -> str:
    chars = string.ascii_uppercase + string.digits
    part1 = ''.join(secrets.choice(chars) for _ in range(4))
    part2 = ''.join(secrets.choice(chars) for _ in range(4))
    return f"AJAX-{part1}-{part2}"

async def create_vouchers(db: AsyncSession, count: int, duration_days: int) -> List[Voucher]:
    vouchers = []
    for _ in range(count):
        code = generate_random_code()
        voucher = Voucher(code=code, duration_days=duration_days, is_redeemed=False)
        db.add(voucher)
        vouchers.append(voucher)
    await db.commit()
    for v in vouchers:
        await db.refresh(v)
    return vouchers

async def redeem_voucher(db: AsyncSession, user: User, code: str) -> bool:
    redeemed_stmt = select(func.count(Voucher.id)).where(Voucher.redeemed_by_id == user.id)
    redeemed_count_res = await db.execute(redeemed_stmt)
    redeemed_count = redeemed_count_res.scalar() or 0
    
    if redeemed_count >= 5:
        return False

    stmt = select(Voucher).where(Voucher.code == code).with_for_update()
    result = await db.execute(stmt)
    voucher = result.scalar_one_or_none()
    
    if not voucher or voucher.is_redeemed:
        return False
        
    voucher.is_redeemed = True
    voucher.redeemed_by_id = user.id
    voucher.redeemed_at = dt_datetime.now(timezone.utc)
    
    now = dt_datetime.now(timezone.utc)
    base_date = now
    if user.subscription_expires_at and user.subscription_expires_at > now:
        base_date = user.subscription_expires_at
        
    user.subscription_expires_at = base_date + timedelta(days=voucher.duration_days)
    user.subscription_status = "active"
    user.subscription_plan = "premium"
    
    await db.commit()
    await db.refresh(user)
    return True

async def get_user_voucher_history(db: AsyncSession, user_id: int) -> List[Voucher]:
    stmt = select(Voucher).where(Voucher.redeemed_by_id == user_id).order_by(Voucher.redeemed_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())

# --- Unified History & Stripe ---

async def get_unified_history(db: AsyncSession, user: User) -> List[BillingHistoryItem]:
    history = []
    try:
        vouchers = await get_user_voucher_history(db, user.id)
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
        logger.error(f"Error fetching local voucher history: {e}")

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
            logger.error(f"Error fetching Stripe invoices: {e}")

    history.sort(key=lambda x: x.date, reverse=True)
    return history
