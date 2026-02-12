import pytest
from backend.app.modules.billing.service import can_access_feature
from backend.app.modules.auth.models import User
from datetime import datetime, timezone, timedelta


class TestPlanPermissions:
    """Test plan-based feature access permissions."""
    
    def test_free_plan_read_only_access(self):
        """Free users should have read-only access to hubs only."""
        user = User(
            email="free@test.com",
            subscription_plan="free",
            subscription_status="active"
        )
        
        # Free tier should only have hub access
        assert can_access_feature(user, "list_hubs") == True
        
        # Free tier should NOT have device/room/group access
        assert can_access_feature(user, "read_devices") == False
        assert can_access_feature(user, "read_rooms") == False
        assert can_access_feature(user, "read_groups") == False
        
        # Free tier should NOT have monitoring or control access
        assert can_access_feature(user, "read_telemetry") == False
        assert can_access_feature(user, "read_logs") == False
        assert can_access_feature(user, "send_commands") == False
        assert can_access_feature(user, "access_proxy") == False
    
    def test_basic_plan_monitoring_access(self):
        """Basic users should have devices/rooms/groups + monitoring access."""
        user = User(
            email="basic@test.com",
            subscription_plan="basic",
            subscription_status="active"
        )
        
        # Basic tier should have hub access
        assert can_access_feature(user, "list_hubs") == True
        
        # Basic tier should have device/room/group access
        assert can_access_feature(user, "read_devices") == True
        assert can_access_feature(user, "read_rooms") == True
        assert can_access_feature(user, "read_groups") == True
        
        # Basic tier should have monitoring features
        assert can_access_feature(user, "read_telemetry") == True
        assert can_access_feature(user, "read_logs") == True
        
        # Basic tier should NOT have control or proxy access
        assert can_access_feature(user, "send_commands") == False
        assert can_access_feature(user, "access_proxy") == False
    
    def test_pro_plan_command_access(self):
        """Pro users should have basic + command access."""
        user = User(
            email="pro@test.com",
            subscription_plan="pro",
            subscription_status="active"
        )
        
        # Pro tier should have all basic features
        assert can_access_feature(user, "list_hubs") == True
        assert can_access_feature(user, "read_devices") == True
        assert can_access_feature(user, "read_rooms") == True
        assert can_access_feature(user, "read_groups") == True
        assert can_access_feature(user, "read_telemetry") == True
        assert can_access_feature(user, "read_logs") == True
        
        # Pro tier should have command access
        assert can_access_feature(user, "send_commands") == True
        
        # Pro tier should NOT have proxy access
        assert can_access_feature(user, "access_proxy") == False
    
    def test_premium_plan_full_access(self):
        """Premium users should have full access to all features."""
        user = User(
            email="premium@test.com",
            subscription_plan="premium",
            subscription_status="active"
        )
        
        # Premium tier should have all features
        assert can_access_feature(user, "list_hubs") == True
        assert can_access_feature(user, "read_devices") == True
        assert can_access_feature(user, "read_rooms") == True
        assert can_access_feature(user, "read_groups") == True
        assert can_access_feature(user, "read_telemetry") == True
        assert can_access_feature(user, "read_logs") == True
        assert can_access_feature(user, "send_commands") == True
        assert can_access_feature(user, "access_proxy") == True
    
    def test_expired_subscription_reverts_to_free(self):
        """Users with expired subscriptions should revert to free tier permissions."""
        user = User(
            email="expired@test.com",
            subscription_plan="premium",
            subscription_status="canceled",
            subscription_expires_at=datetime.now(timezone.utc) - timedelta(days=1)
        )
        
        # Should have free tier permissions only (hubs only)
        assert can_access_feature(user, "list_hubs") == True
        assert can_access_feature(user, "read_devices") == False
        assert can_access_feature(user, "read_logs") == False
        assert can_access_feature(user, "send_commands") == False
        assert can_access_feature(user, "access_proxy") == False
    
    def test_trialing_subscription_has_full_access(self):
        """Users in trial period should have access to their plan features."""
        user = User(
            email="trial@test.com",
            subscription_plan="premium",
            subscription_status="trialing"
        )
        
        # Should have premium access during trial
        assert can_access_feature(user, "access_proxy") == True
        assert can_access_feature(user, "send_commands") == True
    
    def test_unknown_feature_returns_false(self):
        """Unknown features should return False for all plans."""
        user = User(
            email="premium@test.com",
            subscription_plan="premium",
            subscription_status="active"
        )
        
        assert can_access_feature(user, "unknown_feature") == False
        assert can_access_feature(user, "delete_everything") == False
