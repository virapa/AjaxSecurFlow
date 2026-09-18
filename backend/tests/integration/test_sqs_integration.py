import pytest
import pytest_asyncio
from pydantic import SecretStr
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import select
from backend.app.core.config import settings
from backend.app.modules.ajax.models import UserHub
from backend.app.modules.ajax.sqs_service import AjaxEventsConsumer
from backend.app.modules.auth.models import User

@pytest_asyncio.fixture
async def test_user(mock_db):
    user = User(
        email="integration_test@test.com",
        hashed_password="...",
        subscription_status="active",
        subscription_plan="pro"
    )
    mock_db.add(user)
    await mock_db.commit()
    return user

@pytest.mark.asyncio
async def test_user_hub_sync_integration(mock_db, test_user):
    """
    Test that sync_user_hubs correctly populates the UserHub table.
    """
    from backend.app.modules.ajax.service import AjaxClient
    ajax = AjaxClient()
    
    # Mock Ajax API response
    ajax.get_hubs = AsyncMock(return_value=[
        {"hubId": "hub_1", "name": "Casa"},
        {"hubId": "hub_2", "name": "Oficina"}
    ])
    
    # Execute sync
    await ajax.sync_user_hubs(test_user.id, test_user.email)
    
    # Verify mappings in DB mock (mock_db tracks 'added_objects')
    hubs = [obj for obj in mock_db.add.call_args_list if isinstance(obj[0][0], UserHub)]
    assert len(hubs) == 2
    hub_ids = [h[0][0].hub_id for h in hubs]
    assert "hub_1" in hub_ids
    assert "hub_2" in hub_ids

@pytest.mark.asyncio
async def test_find_active_users_for_hub_integration(mock_db, test_user):
    """
    Test that the consumer correctly finds the active users for a given hubId.
    """
    # Mock database query result (result.scalars().unique().all() chain)
    mock_result = MagicMock()
    mock_result.scalars.return_value.unique.return_value.all.return_value = [test_user]
    mock_db.execute = AsyncMock(return_value=mock_result)

    with patch("backend.app.modules.ajax.sqs_service.create_async_engine"), \
         patch("backend.app.modules.ajax.sqs_service.async_sessionmaker") as mock_maker, \
         patch("backend.app.modules.ajax.sqs_service.aioredis"), \
         patch("boto3.client") as mock_boto:
        mock_boto.return_value.get_queue_url.return_value = {"QueueUrl": "http://test-queue"}

        with patch.object(settings, "AWS_KEY_ID", SecretStr("test_key")), \
             patch.object(settings, "AWS_SECRET_KEY", SecretStr("test_secret")), \
             patch.object(settings, "AWS_EVENTS_QUEUE", "test-queue"):
            mock_maker.return_value.return_value.__aenter__.return_value = mock_db
            consumer = AjaxEventsConsumer()

        users = await consumer._find_active_users_for_hub(mock_db, "hub_active")

        assert len(users) == 1
        assert users[0].email == "integration_test@test.com"

        # Verify filtering logic (subscription_status check)
        # The query should include status filter
        stmt = mock_db.execute.call_args[0][0]
        assert "subscription_status" in str(stmt)
