import secrets
import string
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.domain.models import Voucher, User

def generate_random_code() -> str:
    """
    Generates a unique-looking voucher code.
    Format: AJAX-XXXX-XXXX
    """
    chars = string.ascii_uppercase + string.digits
    part1 = ''.join(secrets.choice(chars) for _ in range(4))
    part2 = ''.join(secrets.choice(chars) for _ in range(4))
    return f"AJAX-{part1}-{part2}"

async def create_vouchers(db: AsyncSession, count: int, duration_days: int) -> List[Voucher]:
    """
    Administrative function to mass-generate vouchers.
    """
    vouchers = []
    for _ in range(count):
        # In a high-concurrency real app, we would check for uniqueness collision
        code = generate_random_code()
        voucher = Voucher(code=code, duration_days=duration_days, is_redeemed=False)
        db.add(voucher)
        vouchers.append(voucher)
    await db.commit()
    for v in vouchers:
        await db.refresh(v)
    return vouchers

async def redeem_voucher(db: AsyncSession, user: User, code: str) -> bool:
    """
    Redeems a voucher for a specific user, extending their access.
    """
    stmt = select(Voucher).where(Voucher.code == code, Voucher.is_redeemed == False)
    result = await db.execute(stmt)
    voucher = result.scalar_one_or_none()
    
    if not voucher:
        return False
        
    # 1. Mark voucher as redeemed
    voucher.is_redeemed = True
    voucher.redeemed_by_id = user.id
    voucher.redeemed_at = datetime.now(timezone.utc)
    
    # 2. Extend/Activate user subscription
    now = datetime.now(timezone.utc)
    
    # If user already has an active subscription that hasn't expired, extend from there.
    # Otherwise, start from now.
    base_date = now
    if user.subscription_expires_at and user.subscription_expires_at > now:
        base_date = user.subscription_expires_at
        
    user.subscription_expires_at = base_date + timedelta(days=voucher.duration_days)
    user.subscription_status = "active"
    user.subscription_plan = "premium_voucher" # Distinguish from Stripe plans
    
    await db.commit()
    await db.refresh(user)
    return True
