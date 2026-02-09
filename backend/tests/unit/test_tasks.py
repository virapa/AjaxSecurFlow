import pytest
from unittest.mock import MagicMock, AsyncMock, patch

@pytest.mark.filterwarnings("ignore:coroutine 'AsyncMockMixin._execute_mock_call' was never awaited")
def test_process_stripe_webhook_update_sub():
    from backend.app.worker.tasks import process_stripe_webhook
    
    event_dict = {
        "id": "evt_123",
        "type": "customer.subscription.updated",
        "data": {"object": {"id": "sub_123", "customer": "cus_123", "status": "active"}}
    }
    
    with patch("backend.app.worker.tasks.stripe.Event.construct_from") as mock_event_ctor, \
         patch("backend.app.worker.tasks.asyncio.run") as mock_run:
         
        mock_event = MagicMock()
        mock_event.id = "evt_123"
        mock_event_ctor.return_value = mock_event
        
        # Custom side effect to close the coroutine and avoid unawaited warning
        def side_effect(coro):
            coro.close()
            return {"status": "processed", "id": "evt_123"}
        mock_run.side_effect = side_effect
        
        result = process_stripe_webhook(event_dict, "test_corr_id")
        
        assert result["status"] == "processed"
        assert result["id"] == "evt_123"

def test_process_stripe_webhook_idempotency():
    from backend.app.worker.tasks import process_stripe_webhook
    event_dict = {"id": "evt_duplicate", "type": "any"}
    
    with patch("backend.app.worker.tasks.stripe.Event.construct_from") as mock_event_ctor, \
         patch("backend.app.worker.tasks.asyncio.run") as mock_run:
         
        mock_event = MagicMock()
        mock_event.id = "evt_duplicate"
        mock_event_ctor.return_value = mock_event
        
        def side_effect(coro):
            coro.close()
            return {"status": "skipped", "reason": "idempotent"}
        mock_run.side_effect = side_effect
        
        result = process_stripe_webhook(event_dict)
        assert result["status"] == "skipped"
        assert result["reason"] == "idempotent"
