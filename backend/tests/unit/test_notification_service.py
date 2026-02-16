import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.modules.notifications.service import (
    create_notification,
    get_latest_notifications,
    mark_as_read,
    mark_all_read,
    get_unread_count
)
from backend.app.modules.notifications.models import Notification

@pytest.mark.asyncio
async def test_create_notification():
    mock_db = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_db.execute.return_value = mock_result
    
    user_id = 1
    title = "Test Notification"
    message = "This is a test message"
    
    result = await create_notification(
        db=mock_db,
        user_id=user_id,
        title=title,
        message=message,
        notification_type="security",
        link="/test-link"
    )
    
    assert result.user_id == user_id
    assert result.title == title
    assert result.message == message
    assert result.type == "security"
    assert result.link == "/test-link"
    
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

@pytest.mark.asyncio
async def test_get_latest_notifications():
    mock_db = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    
    # Setup mock return for scalars().all()
    notif1 = Notification(id=1, user_id=1, title="N1", is_read=False)
    notif2 = Notification(id=2, user_id=1, title="N2", is_read=True)
    
    mock_result.scalars.return_value.all.return_value = [notif1, notif2]
    mock_db.execute.return_value = mock_result
    
    notifications = await get_latest_notifications(mock_db, user_id=1)
    
    assert len(notifications) == 2
    assert notifications[0].title == "N1"
    assert mock_db.execute.called

@pytest.mark.asyncio
async def test_mark_as_read_success():
    mock_db = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.rowcount = 1
    mock_db.execute.return_value = mock_result
    
    success = await mark_as_read(mock_db, user_id=1, notification_id=100)
    
    assert success is True
    assert mock_db.commit.called

@pytest.mark.asyncio
async def test_mark_as_read_fail():
    mock_db = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.rowcount = 0
    mock_db.execute.return_value = mock_result
    
    success = await mark_as_read(mock_db, user_id=1, notification_id=100)
    
    assert success is False

@pytest.mark.asyncio
async def test_mark_all_read():
    mock_db = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.rowcount = 5
    mock_db.execute.return_value = mock_result
    
    count = await mark_all_read(mock_db, user_id=1)
    
    assert count == 5
    assert mock_db.commit.called

@pytest.mark.asyncio
async def test_get_unread_count():
    mock_db = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalar.return_value = 3
    mock_db.execute.return_value = mock_result
    
    count = await get_unread_count(mock_db, user_id=1)
    
    assert count == 3
