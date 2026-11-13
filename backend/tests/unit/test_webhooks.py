import pytest
import hmac
import hashlib
import json
from unittest.mock import AsyncMock, patch, MagicMock
from backend.app.modules.ajax.models import UserWebhook
from backend.app.worker.tasks import _dispatch_webhook_logic, _cleanup_old_sqs_events_logic

@pytest.mark.asyncio
async def test_dispatch_webhook_logic_with_hmac():
    webhook = UserWebhook(
        id=1,
        user_id=10,
        hub_id="hub_test",
        target_url="https://homeassistant.local:8123/api/webhook/secret",
        secret_token="super_secret_hmac_key",
        is_active=True
    )

    mock_session = AsyncMock()
    mock_session.get.return_value = webhook

    event_payload = {
        "id": "evt_100",
        "hub_id": "hub_test",
        "event_type": "ALARM",
        "title": "Alarma",
        "timestamp": "2026-09-01T12:00:00Z"
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()

    with patch("backend.app.worker.tasks.async_session_factory") as mock_session_factory, \
         patch("httpx.AsyncClient") as mock_client_cls:

        mock_session_factory.return_value.__aenter__.return_value = mock_session
        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client_cls.return_value.__aenter__.return_value = mock_client_instance

        result = await _dispatch_webhook_logic(None, webhook_id=1, event_payload=event_payload)

        assert result["status"] == "success"
        assert result["status_code"] == 200

        # Verify signature header was sent
        call_args = mock_client_instance.post.call_args
        headers = call_args[1]["headers"]
        assert "X-AjaxSecurFlow-Signature" in headers
        expected_sig = hmac.new(
            b"super_secret_hmac_key",
            json.dumps(event_payload, default=str).encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        assert headers["X-AjaxSecurFlow-Signature"] == f"sha256={expected_sig}"

@pytest.mark.asyncio
async def test_dispatch_webhook_logic_inactive():
    webhook = UserWebhook(
        id=2,
        user_id=10,
        hub_id="hub_test",
        target_url="https://homeassistant.local:8123/api/webhook/secret",
        is_active=False
    )

    mock_session = AsyncMock()
    mock_session.get.return_value = webhook

    with patch("backend.app.worker.tasks.async_session_factory") as mock_session_factory:
        mock_session_factory.return_value.__aenter__.return_value = mock_session
        result = await _dispatch_webhook_logic(None, webhook_id=2, event_payload={})
        assert result["status"] == "skipped"

@pytest.mark.asyncio
async def test_cleanup_old_sqs_events_logic():
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.rowcount = 42
    mock_session.execute.return_value = mock_result

    with patch("backend.app.worker.tasks.async_session_factory") as mock_session_factory:
        mock_session_factory.return_value.__aenter__.return_value = mock_session
        deleted = await _cleanup_old_sqs_events_logic(days=90)
        assert deleted == 42
        assert mock_session.commit.called
