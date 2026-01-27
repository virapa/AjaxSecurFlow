import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.config import settings
from backend.app.domain.models import User

async def activate_subscription(email: str):
    print(f"Connecting to database at {settings.DATABASE_URL}...")
    
    engine = create_async_engine(str(settings.DATABASE_URL))
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print(f"Searching for user: {email}")
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalars().first()

        if not user:
            print(f"❌ User {email} not found.")
            return

        print(f"User found. Current status: {user.subscription_status}")
        
        user.subscription_status = "active"
        user.subscription_id = "sub_manual_override_for_testing"
        user.stripe_customer_id = "cus_manual_override"
        
        await session.commit()
        print(f"✅ subscription_status set to 'active' for {email}")

    await engine.dispose()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python activate_subscription.py <email>")
        # Default to admin user if no arg provided
        target_email = settings.FIRST_SUPERUSER
        print(f"No email provided. Defaulting to: {target_email}")
    else:
        target_email = sys.argv[1]
        
    asyncio.run(activate_subscription(target_email))
