import pytest
import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock
from backend.app.main import app
from backend.app.core.config import settings
from backend.app.api.deps import get_redis
from backend.app.api.v1.auth import get_current_user
from backend.app.domain.models import User
import httpx

# --- Fixtures for this test file ---

@pytest_asyncio.fixture
async def client():
    # Use httpx AsyncClient with the FastAPI app
    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.fixture
def mock_user():
    user = User(
        id=1,
        email="test@example.com",
        hashed_password="hashed",
        is_active=True
    )
    return user

@pytest.fixture
def override_deps(mock_user):
    # Mock Redis (Rate Limiter)
    # We use MagicMock for the client because redis-py pipeline() is synchronous.
    mock_redis = MagicMock()
    mock_redis.get = AsyncMock(return_value=None) # Start with 0 count
    
    mock_pipeline_obj = MagicMock()
    mock_pipeline_obj.execute = AsyncMock()
    mock_pipeline_obj.incr = MagicMock()
    mock_pipeline_obj.expire = MagicMock()
    
    mock_redis.pipeline = MagicMock(return_value=mock_pipeline_obj)
    
    # Mock Current User
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_redis] = lambda: mock_redis
    
    yield mock_redis
    
    app.dependency_overrides = {}

# --- Tests ---

@pytest.mark.asyncio
async def test_support_rate_limit(client, override_deps):
    """
    Test that the support endpoint enforces rate limiting (5 requests/hour).
    """
    mock_redis = override_deps
    
    # Simulate Redis returning count >= 5
    mock_redis.get.return_value = "5"
    
    response = await client.post(
        f"{settings.API_V1_STR}/support/contact",
        json={
            "subject": "Rate Limit",
            "message": "Testing",
            "category": "bug", 
            "email_confirmation": False
        }
    )
    
    assert response.status_code == 429
    assert "Too many support requests" in response.json()["detail"]

@pytest.mark.asyncio
async def test_support_input_validation_max_length(client, override_deps):
    """
    Test that the support endpoint rejects payloads exceeding max length.
    """
    # Create oversize payload
    long_message = "a" * 5001
    
    response = await client.post(
        f"{settings.API_V1_STR}/support/contact",
        json={
            "subject": "Validation",
            "message": long_message,
            "category": "bug",
            "email_confirmation": False
        }
    )
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_support_html_injection(client, override_deps):
    """
    Test that HTML content in subject/message is escaped before sending email.
    """
    with patch("backend.app.api.v1.support.email_service.send_email") as mock_send:
        # Payload with HTML injection attempt
        danger_payload = {
            "subject": "<b>Bold</b>",
            "message": "<script>alert('xss')</script>",
            "category": "bug",
            "email_confirmation": False
        }

        response = await client.post(
            f"{settings.API_V1_STR}/support/contact",
            json=danger_payload
        )
        assert response.status_code == 200

        # Verify email was called
        assert mock_send.called
        
        # Check arguments for escaping
        found_escaped = False
        found_unescaped = False
        
        for call in mock_send.call_args_list:
            kwargs = call.kwargs
            body_html = kwargs.get("body_html", "")
            subject = kwargs.get("subject", "")
            
            # Check for unescaped tags
            if "<script>" in body_html or "<b>" in subject:
                found_unescaped = True
            
            # Check for escaped tags
            if "&lt;script&gt;" in body_html:
                found_escaped = True
                
        assert found_escaped, "Did not find escaped HTML in email body"
        assert not found_unescaped, "Found unescaped HTML in email body/subject"

