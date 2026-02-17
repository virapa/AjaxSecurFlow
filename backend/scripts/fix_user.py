import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
root_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_path))
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
