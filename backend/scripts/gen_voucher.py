import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
root_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_path))

from backend.app.shared.infrastructure.database.session import async_session_factory
from backend.app.modules.billing.service import create_vouchers

async def main():
    async with async_session_factory() as db:
        vouchers = await create_vouchers(db, 1, 30, "basic")
        v = vouchers[0]
        print(f"\n{'='*60}")
        print("VOUCHER GENERADO")
        print(f"{'='*60}")
        print(f"Codigo: {v.code}")
        print(f"Plan: {v.plan.upper()}")
        print(f"Duracion: {v.duration_days} dias")
        print(f"{'='*60}\n")

asyncio.run(main())
