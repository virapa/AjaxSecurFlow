import asyncio
import time
import redis.asyncio as redis
from fastapi import HTTPException, Request, Depends
from backend.app.shared.infrastructure.redis.deps import get_redis
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Fixed Window Rate Limiter using Redis.
    Configurable limit and window.
    """
    def __init__(self, key_prefix: str = "rate_limit", limit: int = 100, window: int = 60):
        self.key_prefix = key_prefix
        self.limit = limit
        self.window = window

    async def __call__(self, request: Request, redis_client: redis.Redis = Depends(get_redis)):
        # Identify user: use user_id from request state if available, else IP
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

class GlobalAjaxRateLimiter:
    """
    Global rate limiter for Ajax API requests.
    When limit is exceeded, requests are queued with an async wait mechanism.
    """
    GLOBAL_COUNTER_KEY = "ajax_api:global_counter"
    GLOBAL_TIMESTAMP_KEY = "ajax_api:window_start"
    
    LIMIT = 100           # Maximum requests per window
    WINDOW = 60           # Window size in seconds
    MAX_WAIT = 30         # Maximum wait time in queue (seconds)
    RETRY_INTERVAL = 0.5  # Check interval when waiting (seconds)
    
    async def __call__(
        self, 
        request: Request, 
        redis_client: redis.Redis = Depends(get_redis)
    ) -> bool:
        start_time = time.time()
        
        while True:
            try:
                current_time = time.time()
                window_start = await redis_client.get(self.GLOBAL_TIMESTAMP_KEY)
                
                if window_start is None:
                    await redis_client.set(self.GLOBAL_TIMESTAMP_KEY, current_time, ex=self.WINDOW)
                    await redis_client.set(self.GLOBAL_COUNTER_KEY, 1, ex=self.WINDOW)
                    return True
                
                window_start = float(window_start)
                
                if current_time - window_start >= self.WINDOW:
                    await redis_client.set(self.GLOBAL_TIMESTAMP_KEY, current_time, ex=self.WINDOW)
                    await redis_client.set(self.GLOBAL_COUNTER_KEY, 1, ex=self.WINDOW)
                    return True
                
                current_count = await redis_client.incr(self.GLOBAL_COUNTER_KEY)
                
                if current_count <= self.LIMIT:
                    return True
                
                await redis_client.decr(self.GLOBAL_COUNTER_KEY)
                
                elapsed = time.time() - start_time
                time_until_reset = self.WINDOW - (current_time - window_start)
                
                if elapsed >= self.MAX_WAIT:
                    raise HTTPException(
                        status_code=503,
                        detail="Service temporarily unavailable. Please try again in a few seconds.",
                        headers={"Retry-After": str(int(min(time_until_reset, 10)))}
                    )
                
                await asyncio.sleep(self.RETRY_INTERVAL)
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Global rate limiter error: {e}")
                return True

# Singleton instances
global_ajax_rate_limiter = GlobalAjaxRateLimiter()
