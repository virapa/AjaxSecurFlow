"""
Global Rate Limiter for Ajax API

Ensures total requests to Ajax API stay under 100/minute across ALL users.
Overflow requests are queued and processed when capacity is available.

Key Features:
- Global counter (not per-user)
- Async queue for overflow requests
- Configurable timeout for queued requests
- Graceful degradation with 503 response
"""

import asyncio
import time
import redis.asyncio as redis
from fastapi import HTTPException, Request, Depends
from backend.app.api.deps import get_redis
import logging

logger = logging.getLogger(__name__)


class GlobalAjaxRateLimiter:
    """
    Global rate limiter for Ajax API requests.
    
    Uses a sliding window algorithm with Redis to track global request count.
    When limit is exceeded, requests are queued with an async wait mechanism.
    """
    
    # Redis keys
    GLOBAL_COUNTER_KEY = "ajax_api:global_counter"
    GLOBAL_TIMESTAMP_KEY = "ajax_api:window_start"
    
    # Limits
    LIMIT = 100           # Maximum requests per window
    WINDOW = 60           # Window size in seconds
    MAX_WAIT = 30         # Maximum wait time in queue (seconds)
    RETRY_INTERVAL = 0.5  # Check interval when waiting (seconds)
    
    async def __call__(
        self, 
        request: Request, 
        redis_client: redis.Redis = Depends(get_redis)
    ) -> bool:
        """
        FastAPI dependency that enforces global rate limiting.
        
        Args:
            request: The incoming FastAPI request
            redis_client: Redis connection
            
        Returns:
            True if request is allowed to proceed
            
        Raises:
            HTTPException 429: If rate limit exceeded and wait timeout expires
            HTTPException 503: If service is temporarily unavailable
        """
        start_time = time.time()
        
        while True:
            try:
                # Get current window and count atomically
                current_time = time.time()
                window_start = await redis_client.get(self.GLOBAL_TIMESTAMP_KEY)
                
                if window_start is None:
                    # First request - initialize window
                    await redis_client.set(self.GLOBAL_TIMESTAMP_KEY, current_time, ex=self.WINDOW)
                    await redis_client.set(self.GLOBAL_COUNTER_KEY, 1, ex=self.WINDOW)
                    logger.debug("Global rate limiter: New window started")
                    return True
                
                window_start = float(window_start)
                
                # Check if window has expired
                if current_time - window_start >= self.WINDOW:
                    # Reset window
                    await redis_client.set(self.GLOBAL_TIMESTAMP_KEY, current_time, ex=self.WINDOW)
                    await redis_client.set(self.GLOBAL_COUNTER_KEY, 1, ex=self.WINDOW)
                    logger.debug("Global rate limiter: Window reset")
                    return True
                
                # Try to increment counter
                current_count = await redis_client.incr(self.GLOBAL_COUNTER_KEY)
                
                if current_count <= self.LIMIT:
                    logger.debug(f"Global rate limiter: {current_count}/{self.LIMIT} requests in window")
                    return True
                
                # Over limit - decrement (we didn't actually use a slot)
                await redis_client.decr(self.GLOBAL_COUNTER_KEY)
                
                # Calculate wait time
                elapsed = time.time() - start_time
                time_until_reset = self.WINDOW - (current_time - window_start)
                
                if elapsed >= self.MAX_WAIT:
                    logger.warning(
                        f"Global rate limiter: Request timed out after {elapsed:.1f}s. "
                        f"Counter at {current_count}/{self.LIMIT}"
                    )
                    raise HTTPException(
                        status_code=503,
                        detail="Service temporarily unavailable. Please try again in a few seconds.",
                        headers={"Retry-After": str(int(min(time_until_reset, 10)))}
                    )
                
                # Wait and retry
                logger.debug(
                    f"Global rate limiter: Queue position, waiting... "
                    f"(elapsed: {elapsed:.1f}s, reset in: {time_until_reset:.1f}s)"
                )
                await asyncio.sleep(self.RETRY_INTERVAL)
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Global rate limiter error: {e}")
                # Fail open - allow request if Redis is unavailable
                # This prevents complete service failure
                return True
        
        return True

    async def get_status(self, redis_client: redis.Redis) -> dict:
        """
        Get current rate limiter status for monitoring.
        
        Returns:
            dict with current_count, limit, window_remaining
        """
        try:
            current_time = time.time()
            window_start = await redis_client.get(self.GLOBAL_TIMESTAMP_KEY)
            current_count = await redis_client.get(self.GLOBAL_COUNTER_KEY)
            
            if window_start is None:
                return {
                    "current_count": 0,
                    "limit": self.LIMIT,
                    "window_remaining": self.WINDOW,
                    "available": self.LIMIT
                }
            
            window_start = float(window_start)
            current_count = int(current_count) if current_count else 0
            window_remaining = max(0, self.WINDOW - (current_time - window_start))
            
            return {
                "current_count": current_count,
                "limit": self.LIMIT,
                "window_remaining": round(window_remaining, 1),
                "available": max(0, self.LIMIT - current_count)
            }
        except Exception as e:
            logger.error(f"Error getting rate limiter status: {e}")
            return {"error": str(e)}


# Singleton instance for use across the application
global_ajax_rate_limiter = GlobalAjaxRateLimiter()
