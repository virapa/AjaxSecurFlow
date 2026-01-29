import pytest
from httpx import AsyncClient
from backend.app.core.config import settings
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
async def test_voucher_flow(async_client: AsyncClient, mock_user_subscription):
    # 1. Generate vouchers (Admin Security Check)
    # We patch settings to include our test user email in ADMIN_EMAILS
    # and define an ADMIN_SECRET_KEY
    mock_settings = MagicMock()
    mock_settings.ADMIN_EMAILS = [mock_user_subscription.email]
    mock_settings.ADMIN_SECRET_KEY.get_secret_value.return_value = "test-admin-secret"
    mock_settings.API_V1_STR = settings.API_V1_STR

    generate_payload = {
        "duration_days": 30,
        "count": 1
    }

    # First attempt: Fail because of missing X-Admin-Secret
    with patch("backend.app.api.v1.auth.settings", mock_settings), \
         patch("backend.app.api.v1.billing.settings", mock_settings):
        
        response = await async_client.post(
            f"{settings.API_V1_STR}/billing/vouchers/generate",
            json=generate_payload
        )
        assert response.status_code == 403

        # Second attempt: Success with correct header
        response = await async_client.post(
            f"{settings.API_V1_STR}/billing/vouchers/generate",
            json=generate_payload,
            headers={"X-Admin-Secret": "test-admin-secret"}
        )
        assert response.status_code == 200
        vouchers = response.json()
        code = vouchers[0]["code"]

        # 2. Redeem voucher (User Action)
        redeem_payload = {"code": code}
        
        # Patch the service for redemption
        with patch("backend.app.services.voucher_service.redeem_voucher", return_value=True):
            response = await async_client.post(
                f"{settings.API_V1_STR}/billing/vouchers/redeem",
                json=redeem_payload
            )
            assert response.status_code == 200
            assert response.json()["status"] == "success"
