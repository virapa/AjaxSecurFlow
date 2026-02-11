import pytest
from datetime import datetime as dt_datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from backend.app.modules.billing import service as billing_service
from backend.app.modules.billing.schemas import VoucherDetailed, BillingHistoryItem

@pytest.mark.asyncio
async def test_get_unified_history_empty():
    """Test history when user has no vouchers and no stripe customer ID."""
    db = AsyncMock()
    user = MagicMock()
    user.id = 1
    user.stripe_customer_id = None
    
    with patch("backend.app.modules.billing.service.get_user_voucher_history", new_callable=AsyncMock, return_value=[]):
        history = await billing_service.get_unified_history(db, user)
        assert history == []

@pytest.mark.asyncio
async def test_get_unified_history_merged_and_sorted():
    """Test merging and sorting of vouchers and invoices."""
    db = AsyncMock()
    user = MagicMock()
    user.id = 1
    user.stripe_customer_id = "cus_123"
    
    now = dt_datetime.now(timezone.utc)
    
    # Mock data
    vouchers = [
        VoucherDetailed(id=1, code="AJAX-1", duration_days=30, is_redeemed=True, redeemed_at=now - timedelta(days=2), created_at=now - timedelta(days=3))
    ]
    
    mock_invoice = MagicMock()
    mock_invoice.id = "in_1"
    mock_invoice.created = int((now - timedelta(days=1)).timestamp())
    mock_invoice.amount_paid = 2999
    mock_invoice.currency = "usd"
    mock_invoice.paid = True
    mock_invoice.invoice_pdf = "http://stripe.com/pdf"
    mock_invoice.lines.data = [MagicMock(description="Premium Plan")]
    
    with patch("backend.app.modules.billing.service.get_user_voucher_history", new_callable=AsyncMock, return_value=vouchers), \
         patch("stripe.Invoice.list") as mock_stripe:
        
        mock_stripe.return_value.data = [mock_invoice]
        
        history = await billing_service.get_unified_history(db, user)
        
        assert len(history) == 2
        # Invoice should be first (1 day ago vs 2 days ago)
        assert history[0].type == "payment"
        assert history[1].type == "voucher"
        assert history[0].amount == "29.99 USD"
        assert history[1].amount == "30 Días"

@pytest.mark.asyncio
async def test_get_unified_history_stripe_failure_graceful():
    """Test that Stripe API failure doesn't break the whole history."""
    db = AsyncMock()
    user = MagicMock()
    user.id = 1
    user.stripe_customer_id = "cus_123"
    
    vouchers = [
        VoucherDetailed(id=1, code="AJAX-1", duration_days=30, is_redeemed=True, redeemed_at=dt_datetime.now(timezone.utc), created_at=dt_datetime.now(timezone.utc))
    ]
    
    with patch("backend.app.modules.billing.service.get_user_voucher_history", return_value=vouchers), \
         patch("stripe.Invoice.list", side_effect=Exception("Stripe Down")):
        
        history = await billing_service.get_unified_history(db, user)
        
        # History should still contain vouchers
        assert len(history) == 1
        assert history[0].type == "voucher"
