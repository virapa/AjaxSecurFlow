"""
Ajax API Response Cache Service

Redis-based caching layer for Ajax API responses with configurable TTLs.
All TTL values are loaded from settings and can be adjusted via environment variables.

Cache Keys Structure:
    ajax:hubs:{user_email}                      - Hub list
    ajax:hub:{user_email}:{hub_id}              - Hub details
    ajax:devices:{user_email}:{hub_id}          - Device list
    ajax:device:{user_email}:{hub_id}:{dev_id}  - Device details
    ajax:rooms:{user_email}:{hub_id}            - Rooms list
    ajax:groups:{user_email}:{hub_id}           - Groups list
"""

import json
import logging
from typing import Any, Callable, Optional
import redis.asyncio as redis

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class AjaxCacheService:
    """
    Redis cache service for Ajax API responses.
    
    Implements get-or-fetch pattern with configurable TTLs.
    TTL values are loaded from settings (environment variables).
    
    Usage:
        cache = AjaxCacheService(redis_client)
        
        # Get cached value or fetch from API
        data = await cache.get_or_fetch(
            key="ajax:hubs:user@email.com",
            ttl=settings.CACHE_TTL_HUBS,
            fetch_func=lambda: ajax_client.get_hubs(user_email)
        )
        
        # Invalidate specific cache
        await cache.invalidate("ajax:hub:user@email.com:HUB123")
        
        # Invalidate all cache for a user
        await cache.invalidate_user("user@email.com")
    """
    
    # Cache key prefixes
    PREFIX_HUBS = "ajax:hubs"
    PREFIX_HUB = "ajax:hub"
    PREFIX_DEVICES = "ajax:devices"
    PREFIX_DEVICE = "ajax:device"
    PREFIX_ROOMS = "ajax:rooms"
    PREFIX_GROUPS = "ajax:groups"
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get cached value by key.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value (deserialized from JSON) or None if not found
        """
        try:
            cached = await self.redis.get(key)
            if cached:
                logger.debug(f"Cache HIT: {key}")
                return json.loads(cached)
            logger.debug(f"Cache MISS: {key}")
            return None
        except Exception as e:
            logger.warning(f"Cache get error for {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int) -> bool:
        """
        Set cache value with TTL.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time-to-live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            serialized = json.dumps(value, default=str)
            await self.redis.set(key, serialized, ex=ttl)
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.warning(f"Cache set error for {key}: {e}")
            return False
    
    async def get_or_fetch(
        self, 
        key: str, 
        ttl: int, 
        fetch_func: Callable
    ) -> Any:
        """
        Get cached value or fetch from API and cache.
        
        This is the main method for caching API responses.
        
        Args:
            key: Cache key
            ttl: Time-to-live in seconds
            fetch_func: Async function to call if cache miss
            
        Returns:
            Cached or freshly fetched value
        """
        # Try cache first
        cached = await self.get(key)
        if cached is not None:
            return cached
        
        # Cache miss - fetch from API
        logger.info(f"Fetching fresh data for: {key}")
        result = await fetch_func()
        
        # Cache the result
        await self.set(key, result, ttl)
        
        return result
    
    async def invalidate(self, key: str) -> bool:
        """
        Invalidate (delete) a specific cache entry.
        
        Args:
            key: Cache key to invalidate
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            deleted = await self.redis.delete(key)
            logger.info(f"Cache INVALIDATE: {key} (deleted: {deleted})")
            return deleted > 0
        except Exception as e:
            logger.warning(f"Cache invalidate error for {key}: {e}")
            return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all cache entries matching a pattern.
        
        Args:
            pattern: Redis key pattern (e.g., "ajax:*:user@email.com:*")
            
        Returns:
            Number of keys deleted
        """
        try:
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                deleted = await self.redis.delete(*keys)
                logger.info(f"Cache INVALIDATE pattern '{pattern}': {deleted} keys deleted")
                return deleted
            return 0
        except Exception as e:
            logger.warning(f"Cache invalidate pattern error for {pattern}: {e}")
            return 0
    
    async def invalidate_user(self, user_email: str) -> int:
        """
        Invalidate all cache entries for a specific user.
        
        Args:
            user_email: User email identifier
            
        Returns:
            Number of keys deleted
        """
        return await self.invalidate_pattern(f"ajax:*:{user_email}*")
    
    async def invalidate_hub(self, user_email: str, hub_id: str) -> int:
        """
        Invalidate all cache entries for a specific hub.
        
        Args:
            user_email: User email identifier
            hub_id: Hub ID
            
        Returns:
            Number of keys deleted
        """
        count = 0
        # Invalidate hub detail
        count += await self.invalidate(f"{self.PREFIX_HUB}:{user_email}:{hub_id}")
        # Invalidate devices list for this hub
        count += await self.invalidate(f"{self.PREFIX_DEVICES}:{user_email}:{hub_id}")
        # Invalidate all device details for this hub
        count += await self.invalidate_pattern(f"{self.PREFIX_DEVICE}:{user_email}:{hub_id}:*")
        return count
    
    # === Convenience methods for specific data types ===
    
    def key_hubs(self, user_email: str) -> str:
        """Generate cache key for hub list."""
        return f"{self.PREFIX_HUBS}:{user_email}"
    
    def key_hub(self, user_email: str, hub_id: str) -> str:
        """Generate cache key for hub detail."""
        return f"{self.PREFIX_HUB}:{user_email}:{hub_id}"
    
    def key_devices(self, user_email: str, hub_id: str) -> str:
        """Generate cache key for device list."""
        return f"{self.PREFIX_DEVICES}:{user_email}:{hub_id}"
    
    def key_device(self, user_email: str, hub_id: str, device_id: str) -> str:
        """Generate cache key for device detail."""
        return f"{self.PREFIX_DEVICE}:{user_email}:{hub_id}:{device_id}"
    
    def key_rooms(self, user_email: str, hub_id: str) -> str:
        """Generate cache key for rooms list."""
        return f"{self.PREFIX_ROOMS}:{user_email}:{hub_id}"
    
    def key_groups(self, user_email: str, hub_id: str) -> str:
        """Generate cache key for groups list."""
        return f"{self.PREFIX_GROUPS}:{user_email}:{hub_id}"
    
    async def get_stats(self) -> dict:
        """
        Get cache statistics for monitoring.
        
        Returns:
            Dict with cache key counts by type
        """
        try:
            stats = {
                "hubs": 0,
                "hub_details": 0,
                "devices": 0,
                "device_details": 0,
                "rooms": 0,
                "groups": 0
            }
            
            async for key in self.redis.scan_iter(match="ajax:*"):
                key_str = key if isinstance(key, str) else key.decode()
                if key_str.startswith(self.PREFIX_HUBS + ":"):
                    stats["hubs"] += 1
                elif key_str.startswith(self.PREFIX_HUB + ":"):
                    stats["hub_details"] += 1
                elif key_str.startswith(self.PREFIX_DEVICES + ":"):
                    stats["devices"] += 1
                elif key_str.startswith(self.PREFIX_DEVICE + ":"):
                    stats["device_details"] += 1
                elif key_str.startswith(self.PREFIX_ROOMS + ":"):
                    stats["rooms"] += 1
                elif key_str.startswith(self.PREFIX_GROUPS + ":"):
                    stats["groups"] += 1
            
            return stats
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"error": str(e)}
