import pytest
from unittest.mock import MagicMock, AsyncMock, patch

@pytest.mark.filterwarnings("ignore:coroutine 'AsyncMockMixin._execute_mock_call' was never awaited")
def test_process_stripe_webhook_update_sub():
    from backend.app.worker.tasks import process_stripe_webhook
    
    # Mock data
    event_dict = {
        "id": "evt_123",
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "id": "sub_123",
                "customer": "cus_123",
                "status": "active"
            }
        }
    }
    
    # Needs to match import path in tasks.py exactly or mock sys modules
    # Easiest way is to patch inside the test functionality
    
    # We need to mock:
    # 1. stripe.Event.construct_from
    # 2. async_session_factory
    # 3. crud_user.get_user...
    # 4. crud_user.update_user...
    
    with patch("backend.app.worker.tasks.stripe.Event.construct_from") as mock_event_ctor, \
         patch("backend.app.worker.tasks.async_session_factory") as mock_session_factory, \
         patch("backend.app.worker.tasks.crud_user") as mock_crud:
         
        # Mock Event object structure
        mock_event = MagicMock()
        mock_event.type = "customer.subscription.updated"
        mock_event.data.object.customer = "cus_123"
        mock_event.data.object.id = "sub_123"
        mock_event.data.object.status = "active"
        mock_event_ctor.return_value = mock_event
        
        # Mock Session
        mock_session = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_session
        
        # Mock User
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_crud.get_user_by_stripe_customer_id = AsyncMock(return_value=mock_user)
        mock_crud.update_user_subscription = AsyncMock()
        
        # Run task
        result = process_stripe_webhook(event_dict)
        
        # Checks
        assert result["status"] == "processed"
        mock_crud.get_user_by_stripe_customer_id.assert_called_with(mock_session, "cus_123")
        mock_crud.update_user_subscription.assert_called_with(
            mock_session, mock_user, "sub_123", "active"
        )
