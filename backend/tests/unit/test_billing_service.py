import pytest
from backend.app.services.billing_service import is_subscription_active
from backend.app.domain.models import User
from unittest.mock import MagicMock, patch

def test_is_subscription_active_true():
    user = User(subscription_status="active")
    with patch("backend.app.services.billing_service.settings") as mock_settings:
        mock_settings.ENABLE_DEVELOPER_MODE = False
        assert is_subscription_active(user) is True
    
    user = User(subscription_status="trialing")
    with patch("backend.app.services.billing_service.settings") as mock_settings:
        mock_settings.ENABLE_DEVELOPER_MODE = False
        assert is_subscription_active(user) is True

def test_is_subscription_active_false():
    user = User(subscription_status="inactive")
    with patch("backend.app.services.billing_service.settings") as mock_settings:
        mock_settings.ENABLE_DEVELOPER_MODE = False
        assert is_subscription_active(user) is False

def test_is_subscription_active_dev_mode():
    user = User(subscription_status="inactive")
    with patch("backend.app.services.billing_service.settings") as mock_settings:
        mock_settings.ENABLE_DEVELOPER_MODE = True
        assert is_subscription_active(user) is True

# We can test the get_user_subscription_status function if it had more logic, 
# but currently it just returns the field.
