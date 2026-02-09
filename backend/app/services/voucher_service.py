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

    Returns:
        str: A randomly generated voucher code.
    """
    chars = string.ascii_uppercase + string.digits
    part1 = ''.join(secrets.choice(chars) for _ in range(4))
    part2 = ''.join(secrets.choice(chars) for _ in range(4))
    return f"AJAX-{part1}-{part2}"

async def create_vouchers(db: AsyncSession, count: int, duration_days: int) -> List[Voucher]:
    """
    Administrative function to mass-generate vouchers.

    Args:
        db: Async database session.
        count: Number of vouchers to create.
        duration_days: How many days of access each voucher provides.

    Returns:
        List[Voucher]: The newly created voucher objects.
    """
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
    """
    Redeems a voucher for a specific user, extending their access.
    
    Business Rules:
    1. Maximum 5 vouchers can be redeemed per account.
    2. Vouchers grant 'premium' plan status.
    3. Duration is additive (extends existing expiration).

    Args:
        db: Async database session.
        user: The user object claiming the voucher.
        code: The unique AJAX-XXXX-XXXX code.

    Returns:
        bool: True if redemption was successful, False if invalid or limit reached.
    """
    # 1. Check Voucher Limit (Max 5 per account)
    from sqlalchemy import func
    redeemed_stmt = select(func.count(Voucher.id)).where(Voucher.redeemed_by_id == user.id)
    redeemed_count_res = await db.execute(redeemed_stmt)
    redeemed_count = redeemed_count_res.scalar() or 0
    
    if redeemed_count >= 5:
        # Limit reached
        return False

    # 2. Find and Validate Voucher
    stmt = select(Voucher).where(Voucher.code == code, Voucher.is_redeemed == False)
    result = await db.execute(stmt)
    voucher = result.scalar_one_or_none()
    
    if not voucher:
        return False
        
    # 3. Mark voucher as redeemed
    voucher.is_redeemed = True
    voucher.redeemed_by_id = user.id
    voucher.redeemed_at = datetime.now(timezone.utc)
    
    # 4. Extend/Activate user subscription
    now = datetime.now(timezone.utc)
    
    base_date = now
    if user.subscription_expires_at and user.subscription_expires_at > now:
        base_date = user.subscription_expires_at
        
    user.subscription_expires_at = base_date + timedelta(days=voucher.duration_days)
    user.subscription_status = "active"
    user.subscription_plan = "premium" # Standardizes to Premium as requested
    
    await db.commit()
    await db.refresh(user)
    return True
async def get_user_voucher_history(db: AsyncSession, user_id: int) -> List[Voucher]:
    """
    Retrieves the redemption history for a specific user.
    """
    stmt = select(Voucher).where(Voucher.redeemed_by_id == user_id).order_by(Voucher.redeemed_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())
