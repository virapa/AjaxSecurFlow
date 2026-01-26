import pytest
import pytest_asyncio
import httpx
from httpx import AsyncClient
from backend.app.main import app
from unittest.mock import AsyncMock, patch, MagicMock

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.fixture
def mock_db():
    mock_session = AsyncMock()
    from backend.app.core.db import get_db
    app.dependency_overrides[get_db] = lambda: mock_session
    yield mock_session
    app.dependency_overrides = {}

@pytest.fixture
def mock_current_user_billed():
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.email = "billed@example.com"
    mock_user.stripe_customer_id = "cus_123"
    
    # Override auth dependency
    from backend.app.api.v1.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_user
    yield mock_user
    app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_create_checkout_session(client, mock_current_user_billed):
    with patch("stripe.checkout.Session.create") as mock_stripe_create, \
         patch("backend.app.core.config.settings.STRIPE_SECRET_KEY", MagicMock(get_secret_value=lambda: "sk_test_123")):
        
        mock_stripe_create.return_value = MagicMock(url="http://stripe.com/checkout")
        
        response = await client.post(
            "/api/v1/billing/create-checkout-session?price_id=price_123"
        )
        
        assert response.status_code == 200
        assert response.json()["url"] == "http://stripe.com/checkout"
        mock_stripe_create.assert_called_once()
        # Verify customer ID was passed
        kwargs = mock_stripe_create.call_args[1]
        assert kwargs["customer"] == "cus_123"

@pytest.mark.asyncio
async def test_stripe_webhook_valid(client):
    # Mock settings
    with patch("backend.app.core.config.settings.STRIPE_WEBHOOK_SECRET", MagicMock(get_secret_value=lambda: "whsec_123")), \
         patch("stripe.Webhook.construct_event") as mock_construct, \
         patch("backend.app.api.v1.billing.process_stripe_webhook.delay") as mock_task:
        
        mock_construct.return_value = MagicMock(to_dict=lambda: {"type": "customer.subscription.created"})
        
        response = await client.post(
            "/api/v1/billing/webhook",
            json={"id": "evt_123", "type": "customer.subscription.created"},
            headers={"Stripe-Signature": "t=123,v1=sig"}
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        mock_task.assert_called_once()

@pytest.mark.asyncio
async def test_stripe_webhook_invalid_signature(client):
    with patch("backend.app.core.config.settings.STRIPE_WEBHOOK_SECRET", MagicMock(get_secret_value=lambda: "whsec_123")), \
         patch("stripe.Webhook.construct_event") as mock_construct:
        
        import stripe
        mock_construct.side_effect = stripe.error.SignatureVerificationError("Invalid sig", "sig_header", "body")
        
        response = await client.post(
            "/api/v1/billing/webhook",
            content=b"payload",
            headers={"Stripe-Signature": "invalid"}
        )
        
        assert response.status_code == 400
        assert "Invalid signature" in response.json()["detail"]
