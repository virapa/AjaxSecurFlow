import pytest
from datetime import datetime as dt_datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from backend.app.modules.billing import service as billing_service
# Note: voucher_service logic was merged into billing_service in the modular architecture
from backend.app.modules.billing import service as voucher_service
from backend.app.modules.auth.models import User
from backend.app.modules.billing.models import Voucher

@pytest.mark.asyncio
async def test_voucher_redemption_limit():
    """
    Test that a user cannot redeem more than 5 vouchers.
    """
    mock_db = AsyncMock()
    user = User(id=1, email="test@example.com", subscription_plan="free")
    
    # Mocking the count result to 5
    mock_result = MagicMock()
    mock_result.scalar.return_value = 5
    mock_db.execute.return_value = mock_result

    # Should return False because limit is 5
    result = await voucher_service.redeem_voucher(mock_db, user, "AJAX-ANY-CODE")
    assert result is False

@pytest.mark.asyncio
async def test_voucher_redemption_allowed_under_limit():
    """
    Test that a user can redeem a voucher if they have less than 5.
    """
    mock_db = AsyncMock()
    user = User(id=1, email="test@example.com", subscription_plan="free", subscription_expires_at=None)
    
    # Mocking the count result to 2
    mock_count_result = MagicMock()
    mock_count_result.scalar.return_value = 2
    
    # Mocking the voucher search result
    mock_voucher = Voucher(id=10, code="AJAX-VALID", is_redeemed=False, duration_days=30)
    mock_voucher_result = MagicMock()
    mock_voucher_result.scalar_one_or_none.return_value = mock_voucher
    
    # Configure execute to return different results for count and select voucher
    mock_db.execute.side_effect = [mock_count_result, mock_voucher_result]

    result = await voucher_service.redeem_voucher(mock_db, user, "AJAX-VALID")
    
    assert result is True
    assert user.subscription_plan == "premium"
    assert user.subscription_status == "active"
    assert user.subscription_expires_at is not None

def test_get_effective_plan_transitions():
    """
    Test the logic of reverting to free when time expires.
    """
    # 1. Expired voucher + No stripe = FREE
    past_date = dt_datetime.now(timezone.utc) - timedelta(days=1)
    user_expired = User(subscription_status="inactive", subscription_expires_at=past_date)
    assert billing_service.get_effective_plan(user_expired) == "free"

    # 2. Active voucher = PREMIUM
    future_date = dt_datetime.now(timezone.utc) + timedelta(days=1)
    user_active_voucher = User(subscription_status="inactive", subscription_expires_at=future_date, subscription_plan="premium")
    assert billing_service.get_effective_plan(user_active_voucher) == "premium"

    # 3. Active Stripe = PREMIUM (regardless of voucher)
    user_stripe = User(subscription_status="active", subscription_expires_at=past_date, subscription_plan="premium")
    assert billing_service.get_effective_plan(user_stripe) == "premium"

    # 4. No anything = FREE
    user_new = User(subscription_status=None, subscription_expires_at=None)
    assert billing_service.get_effective_plan(user_new) == "free"

@pytest.mark.asyncio
async def test_cleanup_expired_task():
    """
    Test that the background task correctly marks expired users as inactive.
    """
    from backend.app.worker.tasks import _cleanup_expired_subscriptions_logic
    
    # We'll use the internal logic function directly in the async test
    with patch("backend.app.worker.tasks.async_session_factory") as mock_factory:
        mock_session = AsyncMock()
        mock_factory.return_value.__aenter__.return_value = mock_session
        
        # Mocking the result of the UPDATE statement
        mock_result = MagicMock()
        mock_result.rowcount = 3
        mock_session.execute.return_value = mock_result
        
        count = await _cleanup_expired_subscriptions_logic()
        
        assert count == 3
        assert mock_session.commit.called
