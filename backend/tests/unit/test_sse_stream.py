"""Unit tests for the /ajax/events/stream SSE generator."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.modules.ajax.router import stream_events


class FakePubSub:
    """Mimics redis.asyncio PubSub: with timeout=0 (default) get_message returns at once."""

    def __init__(self):
        self.calls = []
        self.subscribe = AsyncMock()
        self.unsubscribe = AsyncMock()
        self.close = AsyncMock()

    async def get_message(self, ignore_subscribe_messages=False, timeout=0.0):
        self.calls.append(timeout)
        return None  # nothing published


def _make_deps(disconnect_after: int):
    request = MagicMock()
    checks = {"n": 0}

    async def is_disconnected():
        checks["n"] += 1
        return checks["n"] > disconnect_after

    request.is_disconnected = is_disconnected

    user = MagicMock(id=1, email="sub@example.com")
    pubsub = FakePubSub()
    redis_client = MagicMock()
    redis_client.pubsub.return_value = pubsub

    result = MagicMock()
    result.scalars.return_value.all.return_value = ["00022777"]
    db = AsyncMock()
    db.execute.return_value = result
    return request, user, redis_client, db, pubsub


@pytest.mark.asyncio
async def test_stream_blocks_on_redis_and_sends_keepalive_ping():
    """With no events, the stream must wait on Redis (not busy-loop) and emit pings."""
    request, user, redis_client, db, pubsub = _make_deps(disconnect_after=3)

    with patch("backend.app.modules.ajax.router.billing_service.can_access_feature", return_value=True):
        response = await stream_events(request, user, redis_client, db)
        chunks = [chunk async for chunk in response.body_iterator]

    # Every poll must block on Redis for the keepalive interval instead of returning at once
    assert pubsub.calls, "get_message was never called"
    assert all(t and t > 0 for t in pubsub.calls), f"get_message polled without timeout: {pubsub.calls}"
    # An idle stream emits a keepalive comment on every empty poll
    assert chunks.count(": ping\n\n") == len(pubsub.calls)
    pubsub.unsubscribe.assert_awaited()
    pubsub.close.assert_awaited()
