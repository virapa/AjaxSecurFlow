from datetime import datetime, timezone
from backend.app.modules.auth.models import ApiToken


def test_api_token_is_active_when_not_revoked_and_not_expired():
    token = ApiToken(user_id=1, name="HA", token_hash="abc", prefix="asf_12345678")
    assert token.is_active(datetime.now(timezone.utc)) is True


def test_api_token_inactive_when_revoked():
    now = datetime.now(timezone.utc)
    token = ApiToken(user_id=1, name="HA", token_hash="abc", prefix="asf_12345678", revoked_at=now)
    assert token.is_active(now) is False


def test_api_token_inactive_when_expired():
    now = datetime(2026, 9, 18, tzinfo=timezone.utc)
    token = ApiToken(user_id=1, name="HA", token_hash="abc", prefix="asf_12345678", expires_at=now)
    assert token.is_active(now) is False
