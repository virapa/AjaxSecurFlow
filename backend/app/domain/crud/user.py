import datetime
from typing import Optional, List
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.domain.models import User
from backend.app.core.security import get_password_hash, verify_password

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Fetch a user by email."""
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalars().first()

async def get_user(db: AsyncSession, user_id: int) -> Optional[User]:
    """Fetch a user by primary key."""
    return await db.get(User, user_id)

async def update_user_subscription(
    db: AsyncSession, 
    user_id: int, 
    status: str, 
    plan: str, 
    subscription_id: Optional[str] = None
) -> Optional[User]:
    """Specific operation to update subscription details."""
    user = await get_user(db, user_id)
    if user:
        user.subscription_status = status
        user.subscription_plan = plan
        if subscription_id:
            user.subscription_id = subscription_id
        await db.commit()
        await db.refresh(user)
    return user

async def get_active_users(db: AsyncSession) -> List[User]:
    """Fetch all users with active subscription."""
    result = await db.execute(select(User).filter(User.subscription_status == "active"))
    return list(result.scalars().all())

async def create_user(db: AsyncSession, email: str, password: str) -> User:
    """Create a new user with hashed password."""
    hashed_password = get_password_hash(password)
    new_user = User(email=email, hashed_password=hashed_password)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    """Authenticate a user by email and password."""
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

async def get_user_by_stripe_customer_id(db: AsyncSession, customer_id: str) -> Optional[User]:
    """Fetch user by Stripe Customer ID."""
    result = await db.execute(select(User).filter(User.stripe_customer_id == customer_id))
    return result.scalars().one_or_none()
