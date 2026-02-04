from typing import AsyncGenerator, Optional
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis, from_url

from backend.app.core.db import get_db
from backend.app.core.config import settings
from backend.app.services.ajax_client import AjaxClient

async def get_redis() -> AsyncGenerator[Redis, None]:
    """Redis dependency provider."""
    redis = from_url(
        str(settings.REDIS_URL), 
        encoding="utf-8", 
        decode_responses=True
    )
    try:
        yield redis
    finally:
        await redis.close()

async def get_ajax_client(redis: Redis = Depends(get_redis)) -> AjaxClient:
    """
    AjaxClient provider.
    """
    return AjaxClient(redis_client=redis)
