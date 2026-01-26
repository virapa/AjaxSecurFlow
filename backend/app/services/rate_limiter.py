import redis.asyncio as redis
from fastapi import HTTPException, Request, Depends
from functools import wraps
from backend.app.core.config import settings

# Global Redis pool
redis_pool = None

async def get_redis():
    global redis_pool
    if redis_pool is None:
        redis_pool = redis.from_url(
            str(settings.REDIS_URL), 
            encoding="utf-8", 
            decode_responses=True
        )
    return redis_pool

class RateLimiter:
    """
    Token Bucket Rate Limiter using Redis.
    Configurable limit and window.
    """
    def __init__(self, key_prefix: str = "rate_limit", limit: int = 100, window: int = 60):
        self.key_prefix = key_prefix
        self.limit = limit
        self.window = window

    async def __call__(self, request: Request, redis_client: redis.Redis = Depends(get_redis)):
        # Identify user: in real app, use user_id from auth token. 
        # For now, fallback to IP address or a specific header if no auth.
        user_id = getattr(request.state, "user_id", None)
        if not user_id:
             user_id = request.client.host if request.client else "unknown"

        key = f"{self.key_prefix}:{user_id}"
        
        # Simple Fixed Window implementation
        current_count = await redis_client.incr(key)
        if current_count == 1:
            await redis_client.expire(key, self.window)
            
        if current_count > self.limit:
            raise HTTPException(status_code=429, detail="Too Many Requests")

        return True
