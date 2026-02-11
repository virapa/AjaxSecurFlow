import httpx
import json
import logging
import hashlib
import asyncio
import redis.asyncio as redis
from typing import Optional, Dict, Any, List, Callable
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

class AjaxAuthError(Exception):
    """Custom exception for Ajax Authentication failures."""
    pass

class AjaxCacheService:
    """
    Redis cache service for Ajax API responses.
    """
    PREFIX_HUBS = "ajax:hubs"
    PREFIX_HUB = "ajax:hub"
    PREFIX_DEVICES = "ajax:devices"
    PREFIX_DEVICE = "ajax:device"
    PREFIX_ROOMS = "ajax:rooms"
    PREFIX_GROUPS = "ajax:groups"
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def get(self, key: str) -> Optional[Any]:
        try:
            cached = await self.redis.get(key)
            if cached:
                return json.loads(cached)
            return None
        except Exception as e:
            logger.warning(f"Cache get error for {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int) -> bool:
        try:
            serialized = json.dumps(value, default=str)
            await self.redis.set(key, serialized, ex=ttl)
            return True
        except Exception as e:
            logger.warning(f"Cache set error for {key}: {e}")
            return False
    
    async def get_or_fetch(self, key: str, ttl: int, fetch_func: Callable) -> Any:
        cached = await self.get(key)
        if cached is not None:
            return cached
        result = await fetch_func()
        await self.set(key, result, ttl)
        return result
    
    async def invalidate(self, key: str) -> bool:
        try:
            deleted = await self.redis.delete(key)
            return deleted > 0
        except Exception as e:
            logger.warning(f"Cache invalidate error for {key}: {e}")
            return False

    def key_hubs(self, user_email: str) -> str:
        return f"{self.PREFIX_HUBS}:{user_email}"
    
    def key_hub(self, user_email: str, hub_id: str) -> str:
        return f"{self.PREFIX_HUB}:{user_email}:{hub_id}"
    
    def key_devices(self, user_email: str, hub_id: str) -> str:
        return f"{self.PREFIX_DEVICES}:{user_email}:{hub_id}"
    
    def key_device(self, user_email: str, hub_id: str, device_id: str) -> str:
        return f"{self.PREFIX_DEVICE}:{user_email}:{hub_id}:{device_id}"
    
    def key_rooms(self, user_email: str, hub_id: str) -> str:
        return f"{self.PREFIX_ROOMS}:{user_email}:{hub_id}"
    
    def key_groups(self, user_email: str, hub_id: str) -> str:
        return f"{self.PREFIX_GROUPS}:{user_email}:{hub_id}"

class AjaxClient:
    """
    Async Client for Ajax Systems API.
    """
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client
        self._cache_service: Optional[AjaxCacheService] = None
        self.client = httpx.AsyncClient(
            base_url=settings.AJAX_API_BASE_URL, 
            timeout=15.0
        )
    
    def _get_cache(self) -> AjaxCacheService:
        """Internal helper for testing and lazy init."""
        if not self._cache_service:
            if not self.redis:
                # Fallback to creating a new redis client if none provided
                # In production/FastAPI, it should be provided by Depends(get_redis)
                raise RuntimeError("Redis client not initialized for AjaxClient")
            self._cache_service = AjaxCacheService(self.redis)
        return self._cache_service

    @property
    def cache(self) -> AjaxCacheService:
        return self._get_cache()

    async def _get_ajax_user_id(self, user_email: str) -> Optional[str]:
        return await self.redis.get(f"ajax_user:{user_email}:id")

    async def _get_session_token(self, user_email: str) -> Optional[str]:
        return await self.redis.get(f"ajax_user:{user_email}:token")

    async def _get_refresh_token(self, user_email: str) -> Optional[str]:
        return await self.redis.get(f"ajax_user:{user_email}:refresh")

    async def _save_session_data(
        self, 
        user_email: str, 
        token: str, 
        user_id: str, 
        refresh_token: Optional[str] = None,
        expires_in: int = 3600
    ) -> None:
        await self.redis.set(f"ajax_user:{user_email}:token", token, ex=expires_in - 60)
        await self.redis.set(f"ajax_user:{user_email}:id", user_id)
        if refresh_token:
            await self.redis.set(f"ajax_user:{user_email}:refresh", refresh_token, ex=604800)

    async def login_with_credentials(self, email: str, password_raw: str) -> Dict[str, Any]:
        sha256_hash = hashlib.sha256()
        sha256_hash.update(password_raw.encode('utf-8'))
        password_hash = sha256_hash.hexdigest()
        
        payload = {"login": email, "passwordHash": password_hash, "userRole": "USER"}
        headers = {
            "X-Api-Key": settings.AJAX_API_KEY.get_secret_value(),
            "Content-Type": "application/json",
            "accept": "application/json"
        }
        
        try:
            response = await self.client.post("/login", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            token = data.get("sessionToken")
            user_id = data.get("userId")
            refresh_token = data.get("refreshToken")
            
            if not token or not user_id:
                raise AjaxAuthError("Login successful but missing session data.")
            
            expires_in = data.get("expires_in", 900) 
            await self._save_session_data(email, token, user_id, refresh_token, int(expires_in))
            return data
        except Exception as e:
            logger.error(f"Ajax login failed for {email}: {e}")
            raise AjaxAuthError("Invalid Ajax credentials.")

    async def refresh_session(self, user_email: str) -> str:
        refresh_token = await self._get_refresh_token(user_email)
        user_id = await self._get_ajax_user_id(user_email)
        
        if not refresh_token or not user_id:
            raise AjaxAuthError("No refresh token available.")
            
        payload = {"userId": user_id, "refreshToken": refresh_token}
        headers = {
            "X-Api-Key": settings.AJAX_API_KEY.get_secret_value(),
            "Content-Type": "application/json"
        }
        
        try:
            response = await self.client.post("/refresh", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            new_token = data.get("sessionToken")
            new_refresh = data.get("refreshToken")
            expires_in = data.get("expires_in", 900)
            await self._save_session_data(user_email, new_token, user_id, new_refresh, int(expires_in))
            return new_token
        except Exception as e:
            logger.error(f"Refresh failed for {user_email}: {e}")
            raise AjaxAuthError("Ajax session refresh failed.")

    async def request(self, user_email: str, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        token = await self._get_session_token(user_email)
        if not token:
            token = await self.refresh_session(user_email)

        async def _do_req(current_token: str):
            headers = kwargs.get("headers", {}).copy()
            headers["X-Api-Key"] = settings.AJAX_API_KEY.get_secret_value()
            headers["X-Session-Token"] = current_token
            req_kwargs = kwargs.copy()
            req_kwargs["headers"] = headers
            return await self.client.request(method, endpoint.lstrip("/"), **req_kwargs)

        response = await _do_req(token)
        if response.status_code == 401:
            new_token = await self.refresh_session(user_email)
            response = await _do_req(new_token)
            
        response.raise_for_status()
        return response.json() if response.status_code != 204 else {"success": True}

    async def get_user_info(self, user_email: str) -> Dict[str, Any]:
        user_id = await self._get_ajax_user_id(user_email)
        res = await self.request(user_email, "GET", f"/user/{user_id}")
        # Ensure 'userId' is correctly set to the hex ID
        if not res.get("userId") or "@" in str(res.get("userId")):
            res["userId"] = user_id
        return res

    async def get_hubs(self, user_email: str) -> List[Dict[str, Any]]:
        cache_key = self.cache.key_hubs(user_email)
        cached = await self.cache.get(cache_key)
        if cached: return cached
        
        user_id = await self._get_ajax_user_id(user_email)
        response = await self.request(user_email, "GET", f"/user/{user_id}/hubs")
        
        # Handle both list and dictionary wrapper {"hubs": [...]}
        hubs_list = response.get("hubs", response) if isinstance(response, dict) else response
        
        tasks = [self._fetch_hub_details_uncached(user_email, user_id, h["hubId"]) for h in hubs_list]
        details = await asyncio.gather(*tasks)
        
        # Derive 'online' status from activeChannels availability
        for d in details:
            if "activeChannels" in d:
                d["online"] = bool(d["activeChannels"])

        enriched = [{**h, **d} for h, d in zip(hubs_list, details)]
        await self.cache.set(cache_key, enriched, settings.CACHE_TTL_HUBS)
        return enriched

    async def _fetch_hub_details_uncached(self, user_email: str, user_id: str, hub_id: str) -> Dict[str, Any]:
        """Internal helper for parallel fetching."""
        return await self.request(user_email, "GET", f"/user/{user_id}/hubs/{hub_id}")

    async def get_hub_details(self, user_email: str, hub_id: str) -> Dict[str, Any]:
        user_id = await self._get_ajax_user_id(user_email)
        return await self.cache.get_or_fetch(
            self.cache.key_hub(user_email, hub_id),
            settings.CACHE_TTL_HUB_DETAIL,
            lambda: self.request(user_email, "GET", f"/user/{user_id}/hubs/{hub_id}")
        )
    
    async def get_hub_devices(self, user_email: str, hub_id: str) -> List[Dict[str, Any]]:
        cache_key = self.cache.key_devices(user_email, hub_id)
        cached = await self.cache.get(cache_key)
        if cached: return cached
        
        user_id = await self._get_ajax_user_id(user_email)
        raw = await self.request(user_email, "GET", f"/user/{user_id}/hubs/{hub_id}/devices?enrich=true")
        
        flattened = []
        for item in raw:
            device_id = item.get("deviceId") or item.get("id")
            props = item.get("properties", {})
            # Merge properties but allow root fields to take precedence ONLY if they are not None
            flattened_item = {"deviceId": device_id, **props}
            for field in ["deviceName", "online", "deviceType"]:
                val = item.get(field)
                if val is not None:
                    flattened_item[field] = val
            flattened.append(flattened_item)
            
        await self.cache.set(cache_key, flattened, settings.CACHE_TTL_DEVICES)
    async def get_device_details(self, user_email: str, hub_id: str, device_id: str) -> Dict[str, Any]:
        user_id = await self._get_ajax_user_id(user_email)
        return await self.cache.get_or_fetch(
            self.cache.key_device(user_email, hub_id, device_id),
            settings.CACHE_TTL_DEVICE_DETAIL,
            lambda: self.request(user_email, "GET", f"/user/{user_id}/hubs/{hub_id}/devices/{device_id}")
        )

    async def get_hub_rooms(self, user_email: str, hub_id: str) -> List[Dict[str, Any]]:
        user_id = await self._get_ajax_user_id(user_email)
        return await self.cache.get_or_fetch(
            self.cache.key_rooms(user_email, hub_id),
            settings.CACHE_TTL_ROOMS,
            lambda: self.request(user_email, "GET", f"/user/{user_id}/hubs/{hub_id}/rooms")
        )

    async def get_hub_groups(self, user_email: str, hub_id: str) -> List[Dict[str, Any]]:
        user_id = await self._get_ajax_user_id(user_email)
        return await self.cache.get_or_fetch(
            self.cache.key_groups(user_email, hub_id),
            settings.CACHE_TTL_GROUPS,
            lambda: self.request(user_email, "GET", f"/user/{user_id}/hubs/{hub_id}/groups")
        )

    async def get_room_details(self, user_email: str, hub_id: str, room_id: str) -> Dict[str, Any]:
        user_id = await self._get_ajax_user_id(user_email)
        return await self.request(user_email, "GET", f"/user/{user_id}/hubs/{hub_id}/rooms/{room_id}")

    async def set_arm_state(self, user_email: str, hub_id: str, arm_state: int, group_id: Optional[str] = None) -> Dict[str, Any]:
        user_id = await self._get_ajax_user_id(user_email)
        state_map = {0: "DISARM", 1: "ARM", 2: "NIGHT_MODE_ON"}
        
        endpoint = f"/user/{user_id}/hubs/{hub_id}/commands/arming"
        if group_id:
            endpoint = f"/user/{user_id}/hubs/{hub_id}/groups/{group_id}/commands/arming"
            
        result = await self.request(user_email, "PUT", endpoint, json={"command": state_map[arm_state], "ignoreProblems": True})
        await self.cache.invalidate(self.cache.key_hub(user_email, hub_id))
        await self.cache.invalidate(self.cache.key_hubs(user_email))
        return result

    async def get_hub_logs(self, user_email: str, hub_id: str, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        user_id = await self._get_ajax_user_id(user_email)
        try:
            res = await self.request(
                user_email, 
                "GET", 
                f"/user/{user_id}/hubs/{hub_id}/logs?limit={limit}&offset={offset}"
            )
            # Standardization: Ensure it returns a dict matching EventLogResponse
            if isinstance(res, list):
                return {"logs": res, "total_count": len(res)}
            return res
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Logs not found (404) for hub {hub_id}. This may be normal if no logs exist.")
                return {"logs": [], "total_count": 0}
            raise e

    async def get_user_hub_binding(self, user_email: str, ajax_user_id: str, hub_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the binding information (role) for a specific user and hub.
        """
        try:
            return await self.request(user_email, "GET", f"/user/{ajax_user_id}/hubs/{hub_id}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise e
