import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
root_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_path))

from backend.app.shared.infrastructure.database.session import async_session_factory
from backend.app.modules.auth.models import User
from sqlalchemy import select

async def check(email: str):
    async with async_session_factory() as session:
        res = await session.execute(select(User).where(User.email == email))
        u = res.scalars().first()
        if u:
            print(f'Email: {u.email}')
            print(f'Plan: {u.subscription_plan}')
            print(f'Status: {u.subscription_status}')
            print(f'Expires: {u.subscription_expires_at}')
            print(f'Customer ID: {u.stripe_customer_id}')
        else:
            print(f'User {email} not found')

if __name__ == "__main__":
    email = sys.argv[1] if len(sys.argv) > 1 else 'rpalacios@satyatec.es'
    asyncio.run(check(email))
