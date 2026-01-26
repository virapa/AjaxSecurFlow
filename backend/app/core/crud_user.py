from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.domain.models import User
from backend.app.core.security import get_password_hash, verify_password

async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def create_user(session: AsyncSession, email: str, password: str) -> User:
    hashed_password = get_password_hash(password)
    new_user = User(email=email, hashed_password=hashed_password)
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user

async def authenticate_user(session: AsyncSession, email: str, password: str) -> Optional[User]:
    user = await get_user_by_email(session, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

async def update_user_subscription(
    session: AsyncSession, 
    user: User, 
    subscription_id: str, 
    status: str,
    stripe_customer_id: Optional[str] = None
) -> User:
    user.subscription_id = subscription_id
    user.subscription_status = status
    if stripe_customer_id:
        user.stripe_customer_id = stripe_customer_id
    await session.commit()
    await session.refresh(user)
    return user

async def get_user_by_stripe_customer_id(session: AsyncSession, customer_id: str) -> Optional[User]:
    stmt = select(User).where(User.stripe_customer_id == customer_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
