import pytest
from httpx import AsyncClient
from backend.app.core.config import settings
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_voucher_flow(async_client: AsyncClient, mock_user_subscription):
    # This test verifies that the endpoints exist and have the correct protection.
    
    # 1. Redeem (should be 400 for invalid code)
    # We patch the service to avoid real DB calls since conftest uses MagicMock
    with patch("backend.app.services.voucher_service.redeem_voucher", new_callable=AsyncMock) as mock_redeem:
        mock_redeem.return_value = False
        response = await async_client.post(
            f"{settings.API_V1_STR}/billing/vouchers/redeem",
            json={"code": "INVALID-123"}
        )
        assert response.status_code == 400

    # 2. Generate (should be 403 because we are not sending admin headers/settings)
    response = await async_client.post(
        f"{settings.API_V1_STR}/billing/vouchers/generate",
        json={"duration_days": 30, "count": 1}
    )
    assert response.status_code == 403
