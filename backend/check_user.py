import asyncio
import os
import sys

# Add current dir to path to find backend module
sys.path.append(os.getcwd())

from backend.app.shared.infrastructure.database.session import async_session_factory
from backend.app.modules.auth.models import User
from sqlalchemy import select

async def check():
    async with async_session_factory() as session:
        res = await session.execute(select(User).where(User.email == 'rpalacios@satyatec.es'))
        u = res.scalar_one_or_none()
        if u:
            print(f'Email: {u.email}')
            print(f'Plan: {u.subscription_plan}')
            print(f'Status: {u.subscription_status}')
            print(f'Expires: {u.subscription_expires_at}')
            print(f'Customer ID: {u.stripe_customer_id}')
        else:
            print('User not found')

if __name__ == "__main__":
    asyncio.run(check())
