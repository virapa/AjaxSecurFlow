import json
import pytest
from pydantic import SecretStr
from unittest.mock import MagicMock, patch, AsyncMock
from backend.app.core.config import settings
from backend.app.modules.ajax.sqs_service import AjaxEventsConsumer
from backend.app.modules.ajax.models import AjaxSQSEvent, AjaxHubState

@pytest.fixture
def mock_sqs_client():
    with patch("boto3.client") as mock_client:
        mock_instance = MagicMock()
        mock_instance.get_queue_url.return_value = {"QueueUrl": "http://test-queue"}
        mock_client.return_value = mock_instance
        yield mock_instance

def _result_returning(value):
    """Builds a mock SQLAlchemy Result whose scalar_one_or_none returns `value`."""
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result

def _build_consumer(mock_db):
    with patch("backend.app.modules.ajax.sqs_service.create_async_engine"), \
         patch("backend.app.modules.ajax.sqs_service.async_sessionmaker") as mock_maker, \
         patch("backend.app.modules.ajax.sqs_service.aioredis"), \
         patch.object(settings, "AWS_KEY_ID", SecretStr("test_key")), \
         patch.object(settings, "AWS_SECRET_KEY", SecretStr("test_secret")), \
         patch.object(settings, "AWS_EVENTS_QUEUE", "test-queue"):
        mock_maker.return_value.return_value.__aenter__.return_value = mock_db
        consumer = AjaxEventsConsumer()
        consumer.redis = None  # disable cache invalidation in unit tests
        consumer._find_webhooks_for_hub = AsyncMock(return_value=[])
        return consumer

def _message(message_id: str, receipt: str, event_type: str, hub_id: str, ajax_event_id: str = None, recipient_id: str = "AAA111"):
    """Builds a message with the real Ajax CAPI envelope: {recipient, event}."""
    return {
        "MessageId": message_id,
        "ReceiptHandle": receipt,
        "Body": json.dumps({
            "recipient": {"id": recipient_id, "type": "USER"},
            "event": {
                "eventId": ajax_event_id or f"evt_{message_id}",
                "hubId": hub_id,
                "hubName": "Test Hub",
                "eventType": event_type,
                "eventTypeV2": event_type,
            }
        })
    }

@pytest.mark.asyncio
async def test_process_message_alarm_event(mock_sqs_client, mock_db):
    """
    An ALARM event is audited, stored as last hub state, notifies the user,
    is marked as processed and finally deleted from SQS.
    """
    consumer = _build_consumer(mock_db)

    # 1st execute: event idempotency lookup (miss), 2nd: hub state lookup (miss),
    # 3rd: cross-recipient notification dedup check (miss)
    mock_db.execute = AsyncMock(side_effect=[_result_returning(None), _result_returning(None), _result_returning(None)])

    with patch("backend.app.modules.notifications.service.create_notification", new_callable=AsyncMock) as mock_notify, \
         patch("backend.app.worker.tasks.send_transactional_email.delay"):
        user = MagicMock(id=1, email="test@test.com")
        consumer._find_active_users_for_hub = AsyncMock(return_value=[user])

        await consumer._process_message(_message("msg_123", "receipt_456", "ALARM", "hub_789"))

        # Audit check: raw event + last state persisted
        added = [call[0][0] for call in mock_db.add.call_args_list]
        events = [obj for obj in added if isinstance(obj, AjaxSQSEvent)]
        states = [obj for obj in added if isinstance(obj, AjaxHubState)]
        assert len(events) == 1
        assert len(states) == 1
        assert states[0].hub_id == "hub_789"
        assert states[0].last_event_type == "ALARM"

        # Event marked as processed
        assert events[0].processed_at is not None

        # Notification check
        mock_notify.assert_called_once()
        _, kwargs = mock_notify.call_args
        assert "ALARMA" in kwargs["title"]
        assert kwargs["user_id"] == 1

        # SQS check: message deleted after successful processing
        mock_sqs_client.delete_message.assert_called_once_with(
            QueueUrl="http://test-queue",
            ReceiptHandle="receipt_456"
        )

@pytest.mark.asyncio
async def test_process_message_idempotency(mock_sqs_client, mock_db):
    """
    An already processed message (duplicate MessageId with processed_at set)
    is deleted from SQS without reprocessing.
    """
    consumer = _build_consumer(mock_db)

    existing = MagicMock(spec=AjaxSQSEvent)
    existing.processed_at = "2026-07-08T00:00:00Z"
    mock_db.execute = AsyncMock(return_value=_result_returning(existing))

    await consumer._process_message(_message("duplicate_id", "receipt_789", "ARMED", "hub1"))

    # Should delete from SQS but NOT add to DB
    mock_sqs_client.delete_message.assert_called_once()
    assert mock_db.add.call_count == 0

@pytest.mark.asyncio
async def test_process_message_retry_of_unprocessed_event(mock_sqs_client, mock_db):
    """
    A duplicate message whose stored event was never marked processed
    (e.g. crash mid-processing) is retried: state upserted and notification sent,
    but no duplicate audit row is created.
    """
    consumer = _build_consumer(mock_db)

    existing_event = MagicMock(spec=AjaxSQSEvent)
    existing_event.processed_at = None
    existing_event.id = 42
    existing_state = MagicMock(spec=AjaxHubState)
    mock_db.execute = AsyncMock(side_effect=[
        _result_returning(existing_event),
        _result_returning(existing_state),
        _result_returning(None),  # notification dedup check: not a duplicate
    ])

    with patch("backend.app.modules.notifications.service.create_notification", new_callable=AsyncMock) as mock_notify:
        consumer._find_active_users_for_hub = AsyncMock(return_value=[MagicMock(id=2, email="u@test.com")])

        await consumer._process_message(_message("msg_retry", "receipt_retry", "ARMED", "hub_retry"))

        # No new audit row; existing state mutated in place
        assert mock_db.add.call_count == 0
        assert existing_state.last_event_type == "ARMED"
        assert existing_event.processed_at is not None

        mock_notify.assert_called_once()
        mock_sqs_client.delete_message.assert_called_once()

@pytest.mark.asyncio
async def test_process_message_no_active_subscription(mock_sqs_client, mock_db):
    """
    Events for hubs with no active users are audited and stored as last state,
    but no notification is dispatched. Message is still deleted.
    """
    consumer = _build_consumer(mock_db)

    mock_db.execute = AsyncMock(side_effect=[_result_returning(None), _result_returning(None)])
    consumer._find_active_users_for_hub = AsyncMock(return_value=[])

    with patch("backend.app.modules.notifications.service.create_notification", new_callable=AsyncMock) as mock_notify:
        await consumer._process_message(_message("msg_999", "receipt_999", "ALARM", "hub_unsubscribed"))

        # Audited (event + state added), but no notification
        added = [call[0][0] for call in mock_db.add.call_args_list]
        assert any(isinstance(obj, AjaxSQSEvent) for obj in added)
        assert any(isinstance(obj, AjaxHubState) for obj in added)
        mock_notify.assert_not_called()

        # Message deleted (parsed, audited, and deliberately ignored)
        mock_sqs_client.delete_message.assert_called_once()

@pytest.mark.asyncio
async def test_process_message_skips_duplicate_notification_for_same_ajax_event(mock_sqs_client, mock_db):
    """
    Ajax fans out one SQS message per recipient for the same logical event
    (same event.eventId, different message + recipient). The second message
    must still be audited and update hub state, but must NOT re-notify users.
    """
    consumer = _build_consumer(mock_db)

    # 1st execute: event idempotency lookup (miss - new MessageId),
    # 2nd: hub state lookup (hit - existing state gets updated),
    # 3rd: dedup check - ANOTHER already-processed row shares this ajax_event_id
    already_processed_sibling = MagicMock(spec=AjaxSQSEvent)
    mock_db.execute = AsyncMock(side_effect=[
        _result_returning(None),
        _result_returning(MagicMock(spec=AjaxHubState)),
        _result_returning(already_processed_sibling),
    ])

    with patch("backend.app.modules.notifications.service.create_notification", new_callable=AsyncMock) as mock_notify:
        consumer._find_active_users_for_hub = AsyncMock(return_value=[MagicMock(id=3, email="second_recipient@test.com")])

        await consumer._process_message(
            _message("msg_fanout_2", "receipt_fanout_2", "ALARM", "hub_shared", ajax_event_id="shared_evt_id", recipient_id="BBB222")
        )

        mock_notify.assert_not_called()
        mock_sqs_client.delete_message.assert_called_once()

@pytest.mark.asyncio
async def test_process_message_missing_hub_id(mock_sqs_client, mock_db):
    """
    Messages without hubId are discarded (deleted) without touching the DB.
    """
    consumer = _build_consumer(mock_db)
    mock_db.execute = AsyncMock()

    message = {
        "MessageId": "msg_no_hub",
        "ReceiptHandle": "receipt_no_hub",
        "Body": json.dumps({"type": "ALARM"})
    }
    await consumer._process_message(message)

    mock_sqs_client.delete_message.assert_called_once()
    mock_db.execute.assert_not_called()
    assert mock_db.add.call_count == 0

@pytest.mark.asyncio
async def test_process_message_db_failure_keeps_message(mock_sqs_client, mock_db):
    """
    If persistence fails, the message must NOT be deleted so the SQS
    visibility timeout can retry it.
    """
    consumer = _build_consumer(mock_db)
    mock_db.execute = AsyncMock(side_effect=RuntimeError("db down"))

    await consumer._process_message(_message("msg_fail", "receipt_fail", "ALARM", "hub_x"))

    mock_sqs_client.delete_message.assert_not_called()
