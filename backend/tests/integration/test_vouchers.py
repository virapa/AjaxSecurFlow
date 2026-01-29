import pytest
from httpx import AsyncClient
from backend.app.core.config import settings

@pytest.mark.asyncio
async def test_voucher_flow(async_client: AsyncClient, mock_user_subscription, mock_db):
    # 1. Generate vouchers (as admin/internal)
    generate_payload = {
        "duration_days": 30,
        "count": 2
    }
    # Since generate doesn't have a dependency override yet, it will try to use real DB unless overridden.
    # In conftest.py, mock_db overrides get_db.
    
    response = await async_client.post(
        f"{settings.API_V1_STR}/billing/vouchers/generate",
        json=generate_payload
    )
    assert response.status_code == 200
    vouchers = response.json()
    assert len(vouchers) == 2
    code = vouchers[0]["code"]
    
    # 2. Redeem voucher
    redeem_payload = {"code": code}
    
    # We need to mock the service or ensure the DB mock returns the voucher
    # But for a quick integration test with mocks, we might need to be more specific.
    # Let's mock the voucher_service instead to verify the endpoint logic.
    
    from unittest.mock import patch
    with patch("backend.app.services.voucher_service.redeem_voucher", return_value=True):
        response = await async_client.post(
            f"{settings.API_V1_STR}/billing/vouchers/redeem",
            json=redeem_payload
        )
        assert response.status_code == 200
        assert response.json()["status"] == "success"

    with patch("backend.app.services.voucher_service.redeem_voucher", return_value=False):
        response = await async_client.post(
            f"{settings.API_V1_STR}/billing/vouchers/redeem",
            json=redeem_payload
        )
        assert response.status_code == 400
