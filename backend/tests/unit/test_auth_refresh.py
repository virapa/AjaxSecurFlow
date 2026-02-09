import pytest
import pytest_asyncio
import httpx
import jwt
from httpx import AsyncClient
from backend.app.main import app
from unittest.mock import AsyncMock, patch
from datetime import datetime as dt_datetime, timezone, timedelta
from backend.app.api.deps import get_db, get_redis

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.fixture
def mock_db():
    mock_session = AsyncMock()
    app.dependency_overrides[get_db] = lambda: mock_session
    yield mock_session
    if get_db in app.dependency_overrides:
        del app.dependency_overrides[get_db]

@pytest.mark.asyncio
async def test_refresh_token_rotation_success(client, mock_db):
    """
    Test that a valid refresh token generates a new pair and blacklists the old one.
    """
    from backend.app.core.security import create_refresh_token
    
    user_email = "admin@example.com"
    old_jti = "old-refresh-jti"
    refresh_token = create_refresh_token(subject=user_email, jti=old_jti)
    
    # Mock Redis for blacklist check and setting
    from backend.app.crud import user as crud_user
    
    mock_redis = AsyncMock()
    mock_redis.exists.return_value = False # Not revoked yet
    app.dependency_overrides[get_redis] = lambda: mock_redis
    
    with patch("backend.app.crud.user.get_user_by_email") as mock_get_user:
        
        mock_user = AsyncMock()
        mock_user.email = user_email
        mock_get_user.return_value = mock_user
        
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["refresh_token"] != refresh_token
        
        # Verify rotation (blacklisting old JTI)
        mock_redis.set.assert_called()
        calls = [call[0][0] for call in mock_redis.set.call_args_list]
        assert f"token_blacklist:{old_jti}" in calls
    
    if get_redis in app.dependency_overrides:
        del app.dependency_overrides[get_redis]

@pytest.mark.asyncio
async def test_refresh_token_revoked_fails(client, mock_db):
    """
    Test that a revoked refresh token is rejected.
    """
    from backend.app.core.security import create_refresh_token
    
    user_email = "admin@example.com"
    jti = "revoked-jti"
    refresh_token = create_refresh_token(subject=user_email, jti=jti)
    
    mock_redis = AsyncMock()
    mock_redis.exists.return_value = True # Revoked!
    app.dependency_overrides[get_redis] = lambda: mock_redis
    
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"
    
    if get_redis in app.dependency_overrides:
        del app.dependency_overrides[get_redis]

@pytest.mark.asyncio
async def test_refresh_token_invalid_type_fails(client, mock_db):
    """
    Test that an access token cannot be used in the refresh endpoint.
    """
    from backend.app.core.security import create_access_token
    
    access_token = create_access_token(subject="user@example.com", jti="some-jti")
    
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": access_token}
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"
