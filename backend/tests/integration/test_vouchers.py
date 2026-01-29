import pytest
from httpx import AsyncClient
from backend.app.core.config import settings

@pytest.mark.asyncio
async def test_voucher_flow(async_client: AsyncClient, mock_admin_user, mock_db):
    # 1. Generate vouchers (Requires ADMIN + SECRET)
    generate_payload = {
        "duration_days": 30,
        "count": 2
    }
    
    # Try without secret -> Should fail 422 (FastAPI required header) or 403
    response = await async_client.post(
        f"{settings.API_V1_STR}/billing/vouchers/generate",
        json=generate_payload
    )
    assert response.status_code in [403, 422] 

    # Try with WRONG secret -> Should fail 403
    response = await async_client.post(
        f"{settings.API_V1_STR}/billing/vouchers/generate",
        json=generate_payload,
        headers={"X-Admin-Secret": "wrong_key"}
    )
    assert response.status_code == 403

    # Try with CORRECT secret
    response = await async_client.post(
        f"{settings.API_V1_STR}/billing/vouchers/generate",
        json=generate_payload,
        headers={"X-Admin-Secret": settings.ADMIN_SECRET_KEY.get_secret_value()}
    )
    assert response.status_code == 200
    vouchers = response.json()
    assert len(vouchers) == 2
    code = vouchers[0]["code"]
    
    # 2. Redeem voucher (Uses mock_admin_user as the one who redeems)
    redeem_payload = {"code": code}
    
    from unittest.mock import patch
    with patch("backend.app.services.voucher_service.redeem_voucher", return_value=True):
        response = await async_client.post(
            f"{settings.API_V1_STR}/billing/vouchers/redeem",
            json=redeem_payload
        )
        assert response.status_code == 200
        assert response.json()["status"] == "success"
