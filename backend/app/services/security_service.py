import hashlib
from typing import Optional
from redis.asyncio import Redis
from backend.app.services.rate_limiter import get_redis

# Configuration for Lockout
FAILED_LOGIN_LIMIT = 5
LOCKOUT_DURATION_SECONDS = 900  # 15 minutes

async def check_ip_lockout(ip_address: str) -> bool:
    """
    Checks if an IP address is currently locked out.
    """
    if not ip_address:
        return False
        
    redis_client = await get_redis()
    is_locked = await redis_client.exists(f"lockout:{ip_address}")
    return bool(is_locked)

async def track_login_failure(ip_address: str) -> int:
    """
    Increments the failure counter for an IP and applies lockout if threshold is reached.
    Returns the new failure count.
    """
    if not ip_address:
        return 0
        
    redis_client = await get_redis()
    key = f"failed_attempts:{ip_address}"
    
    # Increment failed attempts
    count = await redis_client.incr(key)
    
    # Set expiration if it's the first failure (e.g., 24h to reset counter)
    if count == 1:
        await redis_client.expire(key, 86400) # 24 hours
        
    # Check if threshold reached
    if count >= FAILED_LOGIN_LIMIT:
        # Create lockout key
        await redis_client.set(f"lockout:{ip_address}", "1", ex=LOCKOUT_DURATION_SECONDS)
        # Optionally reset attempt counter after lockout is applied
        await redis_client.delete(key)
        
    return count

async def reset_login_failures(ip_address: str):
    """
    Clears failed login attempts for an IP after a successful login.
    """
    if not ip_address:
        return
        
    redis_client = await get_redis()
    await redis_client.delete(f"failed_attempts:{ip_address}")
