import pytest
from backend.app.services.billing_service import is_subscription_active
from backend.app.domain.models import User
from unittest.mock import MagicMock

def test_is_subscription_active_true():
    user = User(subscription_status="active")
    assert is_subscription_active(user) is True
    
    user = User(subscription_status="trialing")
    assert is_subscription_active(user) is True

def test_is_subscription_active_false():
    user = User(subscription_status="inactive")
    assert is_subscription_active(user) is False
    
    user = User(subscription_status="canceled")
    assert is_subscription_active(user) is False
    
    user = User(subscription_status=None)
    assert is_subscription_active(user) is False

# We can test the get_user_subscription_status function if it had more logic, 
# but currently it just returns the field.
