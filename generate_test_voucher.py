"""
Script to generate a voucher for testing plan restrictions.
Usage: python generate_test_voucher.py
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from backend.app.shared.infrastructure.database.session import get_db_session
from backend.app.modules.billing.service import create_vouchers


async def main():
    """Generate a single Basic plan voucher for testing."""
    async for db in get_db_session():
        vouchers = await create_vouchers(
            db=db,
            count=1,
            duration_days=30,
            plan="basic"
        )
        
        print("\n" + "="*60)
        print("✅ VOUCHER GENERADO EXITOSAMENTE")
        print("="*60)
        print(f"\n📋 Código: {vouchers[0].code}")
        print(f"📦 Plan: {vouchers[0].plan.upper()}")
        print(f"⏰ Duración: {vouchers[0].duration_days} días")
        print(f"🔑 ID: {vouchers[0].id}")
        print("\n" + "="*60)
        print("\n💡 Para canjear este voucher:")
        print("   1. Ve a http://localhost:3000/billing")
        print("   2. Ingresa el código en el campo de voucher")
        print("   3. Haz clic en 'Canjear'")
        print("\n")
        break


if __name__ == "__main__":
    asyncio.run(main())
