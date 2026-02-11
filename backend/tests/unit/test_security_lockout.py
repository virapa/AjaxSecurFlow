import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException
from backend.app.modules.security import service as security_service

@pytest.mark.asyncio
async def test_track_login_failure_increments_and_bans():
    """
    Test that multiple failures lead to a lockout.
    """
    mock_redis = AsyncMock()
    # Simulate counts: 1, 2, 3, 4, 5
    mock_redis.incr.side_effect = [1, 2, 3, 4, 5]
    mock_redis.exists.return_value = False
    
    # 4 attempts should not ban
    for i in range(4):
        count = await security_service.track_login_failure("127.0.0.1", mock_redis)
        assert count == i + 1
        mock_redis.set.assert_not_called()
        
    # 5th attempt should ban
    count = await security_service.track_login_failure("127.0.0.1", mock_redis)
    assert count == 5
    mock_redis.set.assert_called_with("lockout:127.0.0.1", "1", ex=900)
    mock_redis.delete.assert_called_with("failed_attempts:127.0.0.1")

@pytest.mark.asyncio
async def test_check_ip_lockout_returns_true_if_banned():
    """
    Test that check_ip_lockout correctly identifies a banned IP.
    """
    mock_redis = AsyncMock()
    mock_redis.exists.return_value = True
    
    is_locked = await security_service.check_ip_lockout("1.2.3.4", mock_redis)
    assert is_locked is True
    mock_redis.exists.assert_called_with("lockout:1.2.3.4")

@pytest.mark.asyncio
async def test_reset_login_failures_deletes_key():
    """
    Test that reset_login_failures clears the counters.
    """
    mock_redis = AsyncMock()
    
    await security_service.reset_login_failures("1.1.1.1", mock_redis)
    mock_redis.delete.assert_called_with("failed_attempts:1.1.1.1")
