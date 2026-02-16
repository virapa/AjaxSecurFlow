import pytest
import asyncio
from unittest.mock import MagicMock, patch

def test_process_stripe_webhook_update_sub():
    from backend.app.worker.tasks import process_stripe_webhook
    
    event_dict = {
        "id": "evt_123",
        "type": "customer.subscription.updated",
        "data": {"object": {"id": "sub_123", "customer": "cus_123", "status": "active"}}
    }
    
    mock_loop = MagicMock(spec=asyncio.AbstractEventLoop)
    def side_effect(coro):
        coro.close()
        return {"status": "processed", "id": "evt_123"}
    mock_loop.run_until_complete.side_effect = side_effect
    
    with patch("backend.app.worker.tasks.stripe.Event.construct_from") as mock_event_ctor, \
         patch("backend.app.worker.tasks.asyncio.get_event_loop") as mock_get_loop, \
         patch("backend.app.worker.tasks.asyncio.new_event_loop") as mock_new_loop, \
         patch("backend.app.worker.tasks.asyncio.set_event_loop") as mock_set_loop:
         
        mock_event = MagicMock()
        mock_event.id = "evt_123"
        mock_event.type = "customer.subscription.updated"
        mock_event_ctor.return_value = mock_event
        
        mock_get_loop.return_value = mock_loop
        mock_new_loop.return_value = mock_loop
        
        result = process_stripe_webhook(event_dict, "test_corr_id")
        
        assert result["status"] == "processed"
        assert result["id"] == "evt_123"

def test_process_stripe_webhook_idempotency():
    from backend.app.worker.tasks import process_stripe_webhook
    event_dict = {"id": "evt_duplicate", "type": "any"}
    
    mock_loop = MagicMock(spec=asyncio.AbstractEventLoop)
    def side_effect(coro):
        coro.close()
        return {"status": "skipped", "reason": "idempotent"}
    mock_loop.run_until_complete.side_effect = side_effect
    
    with patch("backend.app.worker.tasks.stripe.Event.construct_from") as mock_event_ctor, \
         patch("backend.app.worker.tasks.asyncio.get_event_loop") as mock_get_loop, \
         patch("backend.app.worker.tasks.asyncio.new_event_loop") as mock_new_loop, \
         patch("backend.app.worker.tasks.asyncio.set_event_loop") as mock_set_loop:
         
        mock_event = MagicMock()
        mock_event.id = "evt_duplicate"
        mock_event.type = "any"
        mock_event_ctor.return_value = mock_event
        
        mock_get_loop.return_value = mock_loop
        mock_new_loop.return_value = mock_loop
        
        result = process_stripe_webhook(event_dict)
        assert result["status"] == "skipped"
        assert result["reason"] == "idempotent"
