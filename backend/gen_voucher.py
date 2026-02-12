import asyncio
from backend.app.modules.billing.service import create_vouchers
from backend.app.shared.infrastructure.database.session import async_session_factory

async def gen():
    async with async_session_factory() as db:
        v = await create_vouchers(db, 1, 30, "basic")
        print(f"CODE:{v[0].code}")

if __name__ == "__main__":
    asyncio.run(gen())
