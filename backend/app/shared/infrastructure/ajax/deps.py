from fastapi import Depends
from redis.asyncio import Redis
from backend.app.modules.ajax.service import AjaxClient
from backend.app.shared.infrastructure.redis.deps import get_redis

async def get_ajax_client(redis: Redis = Depends(get_redis)) -> AjaxClient:
    """
    AjaxClient provider.
    """
    return AjaxClient(redis_client=redis)
