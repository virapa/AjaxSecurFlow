import asyncio
import os
import sys
sys.path.append(os.getcwd())
from backend.app.shared.infrastructure.database.session import async_session_factory
from backend.app.modules.auth.models import User
from sqlalchemy import update

async def fix():
    async with async_session_factory() as session:
        await session.execute(update(User).where(User.email == 'rpalacios@satyatec.es').values(subscription_status='active'))
        await session.commit()
    print('User updated to active in DB')

if __name__ == "__main__":
    asyncio.run(fix())
