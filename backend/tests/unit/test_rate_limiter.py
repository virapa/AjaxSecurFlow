import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException, Request
from backend.app.services.rate_limiter import RateLimiter

@pytest.mark.asyncio
async def test_rate_limiter_allow():
    # Setup
    mock_redis = AsyncMock()
    mock_redis.incr.return_value = 1 # First request
    
    limiter = RateLimiter(limit=10, window=60)
    mock_request = AsyncMock(spec=Request)
    # Fix: Ensure user_id is explicitly None so getattr(state, ...) works as expected or we mock attributes
    mock_request.state.user_id = None
    mock_request.client.host = "127.0.0.1"
    
    # Act
    result = await limiter(mock_request, redis_client=mock_redis)
    
    # Assert
    assert result is True
    mock_redis.incr.assert_called_once()
    mock_redis.expire.assert_called_once_with("rate_limit:127.0.0.1", 60)

@pytest.mark.asyncio
async def test_rate_limiter_block():
    # Setup
    mock_redis = AsyncMock()
    mock_redis.incr.return_value = 11 # Exceeds limit of 10
    
    limiter = RateLimiter(limit=10, window=60)
    mock_request = AsyncMock(spec=Request)
    mock_request.state.user_id = None
    mock_request.client.host = "127.0.0.1"
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc:
        await limiter(mock_request, redis_client=mock_redis)
    
    assert exc.value.status_code == 429
    assert exc.value.detail == "Too Many Requests"

@pytest.mark.asyncio
async def test_rate_limiter_user_id_priority():
    # Setup
    mock_redis = AsyncMock()
    mock_redis.incr.return_value = 1
    
    limiter = RateLimiter()
    mock_request = AsyncMock(spec=Request)
    # Simulate authenticated user
    mock_request.state.user_id = "user_123" 
    mock_request.client.host = "127.0.0.1"
    
    # Act
    await limiter(mock_request, redis_client=mock_redis)
    
    # Assert
    # Check that the key used includes the user_id, NOT the IP
    args, _ = mock_redis.incr.call_args
    assert args[0] == "rate_limit:user_123"
