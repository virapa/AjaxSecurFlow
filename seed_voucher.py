import asyncio
import sys
import os

# Adición del path para que Python encuentre los módulos de backend
sys.path.append("/app")

from backend.app.modules.billing.models import Voucher
from backend.app.shared.infrastructure.database.session import async_session_factory

async def seed():
    print("Iniciando seeding de voucher manual...")
    async with async_session_factory() as db:
        try:
            voucher = Voucher(
                code="AJAX-BASI-2026",
                duration_days=365,
                plan="basic",
                is_redeemed=False
            )
            db.add(voucher)
            await db.commit()
            print("Voucher AJAX-BASI-2026 creado exitosamente (manual).")
        except Exception as e:
            print(f"Error al crear voucher: {e}")

if __name__ == "__main__":
    asyncio.run(seed())
