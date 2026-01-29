import pytest
from httpx import AsyncClient
from backend.app.core.config import settings
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_notification_flow(async_client: AsyncClient, mock_user_subscription, mock_db):
    # Setup mocks correctly for AsyncSession
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars
    mock_result.scalar.return_value = 0
    
    mock_db.execute = AsyncMock(return_value=mock_result)

    # 1. Check summary
    response = await async_client.get(f"{settings.API_V1_STR}/notifications/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["unread_count"] == 0
    assert len(data["notifications"]) == 0

    # 2. Test Mark All as Read
    response = await async_client.post(f"{settings.API_V1_STR}/notifications/mark-all-read")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
