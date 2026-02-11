from typing import AsyncGenerator
from redis.asyncio import Redis, from_url
from backend.app.core.config import settings

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
