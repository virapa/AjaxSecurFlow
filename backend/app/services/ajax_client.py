import httpx
import redis.asyncio as redis
import logging
from typing import Optional, Dict, Any, List
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from backend.app.core.config import settings
from backend.app.services.ajax_cache import AjaxCacheService

# Logging
logger = logging.getLogger(__name__)

class AjaxAuthError(Exception):
    """Custom exception for Ajax Authentication failures."""
    pass

class AjaxClient:
    """
    Async Client for Ajax Systems API.
    Handles Authentication (Session Token) with Redis Caching and Automatic Renewal.
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client
        self._cache: Optional[AjaxCacheService] = None
        # Initialize HTTP client with base URL from settings
        self.client = httpx.AsyncClient(
            base_url=settings.AJAX_API_BASE_URL, 
            timeout=15.0
        )
    
    async def _get_cache(self) -> AjaxCacheService:
        """Get or initialize cache service."""
        if not self._cache:
            redis_client = await self._get_redis()
            self._cache = AjaxCacheService(redis_client)
        return self._cache

    async def _get_redis(self) -> redis.Redis:
        if not self.redis:
            # Fallback for manual instantiation if absolutely necessary
            self.redis = redis.from_url(
                str(settings.REDIS_URL), 
                encoding="utf-8", 
                decode_responses=True
            )
        return self.redis

    async def _get_ajax_user_id(self, user_email: str) -> Optional[str]:
        """
        Retrieve the cached Ajax userId for a specific user.

        Args:
            user_email: The email of the user as unique identifier.

        Returns:
            Optional[str]: The Ajax userId if found in cache.
        """
        redis_client = await self._get_redis()
        return await redis_client.get(f"ajax_user:{user_email}:id")

    async def _get_session_token(self, user_email: str) -> Optional[str]:
        """Retrieve cached session token."""
        redis_client = await self._get_redis()
        return await redis_client.get(f"ajax_user:{user_email}:token")

    async def _get_refresh_token(self, user_email: str) -> Optional[str]:
        """Retrieve cached refresh token."""
        redis_client = await self._get_redis()
        return await redis_client.get(f"ajax_user:{user_email}:refresh")

    async def _save_session_data(
        self, 
        user_email: str, 
        token: str, 
        user_id: str, 
        refresh_token: Optional[str] = None,
        expires_in: int = 3600
    ) -> None:
        """
        Save session token, userId and refreshToken to Redis.
        """
        redis_client = await self._get_redis()
        # Session token expires in 15min typically, Refresh in 7 days
        # Buffer of 60 seconds for safety
        await redis_client.set(f"ajax_user:{user_email}:token", token, ex=expires_in - 60)
        await redis_client.set(f"ajax_user:{user_email}:id", user_id) # ID doesn't need to expire quickly
        
        if refresh_token:
            # 7 days = 604800 seconds
            await redis_client.set(f"ajax_user:{user_email}:refresh", refresh_token, ex=604800)

    async def login_with_credentials(self, email: str, password_raw: str) -> Dict[str, Any]:
        """
        Authenticate with Ajax Systems using dynamic user credentials.
        This is the core of the Unified Login system.

        Args:
            email: User's Ajax email.
            password_raw: User's Ajax password (plain text, will be hashed).

        Returns:
            Dict[str, Any]: The login response from Ajax Systems.

        Raises:
            AjaxAuthError: If the credentials are rejected or response is incomplete.
        """
        import hashlib
        
        sha256_hash = hashlib.sha256()
        sha256_hash.update(password_raw.encode('utf-8'))
        password_hash = sha256_hash.hexdigest()
        
        payload = {
            "login": email,
            "passwordHash": password_hash,
            "userRole": "USER" 
        }
        
        headers = {
            "X-Api-Key": settings.AJAX_API_KEY.get_secret_value(),
            "Content-Type": "application/json",
            "accept": "application/json"
        }
        
        try:
            logger.info(f"Verifying Ajax credentials for user: {email}")
            response = await self.client.post("/login", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            token = data.get("sessionToken")
            user_id = data.get("userId")
            refresh_token = data.get("refreshToken")
            
            if not token or not user_id:
                raise AjaxAuthError("Login successful but missing session data.")
                
            # Swagger says 15 mins (900s), default to 3600 if totally missing
            expires_in = data.get("expires_in", 900) 
            await self._save_session_data(email, token, user_id, refresh_token, int(expires_in))
            return data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Ajax validation failed for {email}: {e.response.text}")
            raise AjaxAuthError("Invalid Ajax credentials.")
        except Exception as e:
            logger.error(f"Error during Ajax credential validation: {e}")
            raise

    async def refresh_session(self, user_email: str) -> str:
        """
        Obtain a new session token using the cached refresh token.
        
        Returns:
            str: The new session token.
        """
        refresh_token = await self._get_refresh_token(user_email)
        user_id = await self._get_ajax_user_id(user_email)
        
        if not refresh_token or not user_id:
            raise AjaxAuthError("No refresh token available. Re-login required.")
            
        payload = {
            "userId": user_id,
            "refreshToken": refresh_token
        }
        
        headers = {
            "X-Api-Key": settings.AJAX_API_KEY.get_secret_value(),
            "Content-Type": "application/json"
        }
        
        try:
            logger.info(f"Refreshing Ajax session for {user_email}")
            response = await self.client.post("/refresh", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            new_token = data.get("sessionToken")
            new_refresh = data.get("refreshToken")
            
            if not new_token:
                raise AjaxAuthError("Refresh successful but missing new session token.")
                
            expires_in = data.get("expires_in", 900)
            await self._save_session_data(user_email, new_token, user_id, new_refresh, int(expires_in))
            return new_token
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Refresh failed for {user_email}: {e.response.text}")
            raise AjaxAuthError("Ajax session refresh failed. Please log in again.")
        except Exception as e:
            logger.error(f"Unexpected error during refresh: {e}")
            raise

    async def request(self, user_email: str, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Execute an authenticated HTTP request for a specific user using their cached session.

        Args:
            user_email: Identifier for the user's session cache.
            method: HTTP method (GET, POST, etc.).
            endpoint: The API endpoint path.
            **kwargs: Extra arguments for the HTTP client.

        Returns:
            Dict[str, Any]: JSON response from the API.

        Raises:
            AjaxAuthError: If the session is expired or invalid.
        """
        token = await self._get_session_token(user_email)
        
        if not token:
            try:
                # Attempt to refresh if token is not in cache (could have just expired)
                token = await self.refresh_session(user_email)
            except AjaxAuthError:
                raise AjaxAuthError("Session expired. Please log in again.")

        async def _do_req(current_token: str):
            headers = kwargs.get("headers", {}).copy()
            headers["X-Api-Key"] = settings.AJAX_API_KEY.get_secret_value()
            headers["X-Session-Token"] = current_token
            headers["accept"] = "application/json"
            req_kwargs = kwargs.copy()
            req_kwargs["headers"] = headers
            
            # Ensure safe URL joining: make endpoint relative to base_url if it's meant to be appended
            safe_endpoint = endpoint.lstrip("/")
            return await self.client.request(method, safe_endpoint, **req_kwargs)

        try:
            response = await _do_req(token)
            
            if response.status_code == 401:
                # Token might have expired just now. Attempt ONE refresh.
                logger.info(f"Session expired (401) for {user_email}, attempting refresh...")
                new_token = await self.refresh_session(user_email)
                response = await _do_req(new_token)
            
            if response.status_code == 401:
                raise AjaxAuthError("Ajax session expired.")
            
            response.raise_for_status()
            
            # Handle 204 No Content (common for security commands)
            if response.status_code == 204:
                return {"success": True}
                
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"API request failed: {e.response.text}")
            raise

    async def _ensure_user_id(self, user_email: str) -> str:
        """
        Verify that a userId exists in the cache for the given user.

        Args:
            user_email: User's identifier.

        Returns:
            str: The cached userId.

        Raises:
            AjaxAuthError: If no session is found.
        """
        user_id = await self._get_ajax_user_id(user_email)
        if not user_id:
            raise AjaxAuthError("No active Ajax session for this user.")
        return user_id

    async def get_user_info(self, user_email: str) -> Dict[str, Any]:
        """Get general info for the user."""
        user_id = await self._ensure_user_id(user_email)
        return await self.request(user_email, "GET", f"/user/{user_id}")

    async def get_hubs(self, user_email: str) -> List[Dict[str, Any]]:
        """
        Get hubs for user with enriched detail.
        The base Ajax list endpoint only returns IDs, so we fetch details 
        for each hub to provide a rich dashboard experience.
        Results are cached for performance.
        """
        cache = await self._get_cache()
        cache_key = cache.key_hubs(user_email)
        
        # Check cache first
        cached = await cache.get(cache_key)
        if cached is not None:
            return cached
        
        # Cache miss - fetch from API
        import asyncio
        user_id = await self._ensure_user_id(user_email)
        hubs_list = await self.request(user_email, "GET", f"/user/{user_id}/hubs")
        
        if not isinstance(hubs_list, list):
            return []
            
        # Fetch details for each hub in parallel for efficiency
        tasks = [self._fetch_hub_details_uncached(user_email, h.get('hubId')) for h in hubs_list if h.get('hubId')]
        details = await asyncio.gather(*tasks, return_exceptions=True)
        
        enriched_hubs = []
        for i, hub_summary in enumerate(hubs_list):
            detail = details[i]
            if isinstance(detail, Exception):
                logger.error(f"Failed to fetch details for hub {hub_summary.get('hubId')}: {detail}")
                hub_data = hub_summary
            else:
                hub_data = {**hub_summary, **detail}
            
            if hub_data.get('online') is None:
                active_channels = hub_data.get('activeChannels', [])
                has_state = hub_data.get('state') is not None
                hub_data['online'] = len(active_channels) > 0 or has_state
                
            enriched_hubs.append(hub_data)
        
        # Cache the result
        await cache.set(cache_key, enriched_hubs, settings.CACHE_TTL_HUBS)
        return enriched_hubs
    
    async def _fetch_hub_details_uncached(self, user_email: str, hub_id: str) -> Dict[str, Any]:
        """Internal method to fetch hub details without caching (used by get_hubs)."""
        user_id = await self._ensure_user_id(user_email)
        return await self.request(user_email, "GET", f"/user/{user_id}/hubs/{hub_id}")

    async def get_hub_details(self, user_email: str, hub_id: str) -> Dict[str, Any]:
        """Get hub detail with caching."""
        cache = await self._get_cache()
        cache_key = cache.key_hub(user_email, hub_id)
        
        return await cache.get_or_fetch(
            key=cache_key,
            ttl=settings.CACHE_TTL_HUB_DETAIL,
            fetch_func=lambda: self._fetch_hub_details_uncached(user_email, hub_id)
        )

    async def get_hub_logs(self, user_email: str, hub_id: str, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Get hub event logs."""
        user_id = await self._ensure_user_id(user_email)
        params = {"limit": limit, "offset": offset}
        return await self.request(user_email, "GET", f"/user/{user_id}/hubs/{hub_id}/logs", params=params)

    async def get_hub_groups(self, user_email: str, hub_id: str) -> Dict[str, Any]:
        """Get hub security groups with caching."""
        cache = await self._get_cache()
        cache_key = cache.key_groups(user_email, hub_id)
        
        async def fetch():
            user_id = await self._ensure_user_id(user_email)
            return await self.request(user_email, "GET", f"/user/{user_id}/hubs/{hub_id}/groups")
        
        return await cache.get_or_fetch(cache_key, settings.CACHE_TTL_GROUPS, fetch)

    async def get_hub_rooms(self, user_email: str, hub_id: str) -> List[Dict[str, Any]]:
        """Get list of rooms for a specific hub with caching."""
        cache = await self._get_cache()
        cache_key = cache.key_rooms(user_email, hub_id)
        
        async def fetch():
            user_id = await self._ensure_user_id(user_email)
            response = await self.request(user_email, "GET", f"/user/{user_id}/hubs/{hub_id}/rooms")
            return response if isinstance(response, list) else response.get("rooms", [])
        
        return await cache.get_or_fetch(cache_key, settings.CACHE_TTL_ROOMS, fetch)

    async def get_room_details(self, user_email: str, hub_id: str, room_id: str) -> Dict[str, Any]:
        """Get detailed info for a specific room."""
        user_id = await self._ensure_user_id(user_email)
        return await self.request(user_email, "GET", f"/user/{user_id}/hubs/{hub_id}/rooms/{room_id}")

    async def get_hub_devices(self, user_email: str, hub_id: str) -> List[Dict[str, Any]]:
        """Get hub devices with enriched state, flattened for easy use. Cached."""
        cache = await self._get_cache()
        cache_key = cache.key_devices(user_email, hub_id)
        
        # Check cache first
        cached = await cache.get(cache_key)
        if cached is not None:
            return cached
        
        # Cache miss - fetch from API
        user_id = await self._ensure_user_id(user_email)
        endpoint = f"/user/{user_id}/hubs/{hub_id}/devices?enrich=true"
        logger.info(f"Requesting devices from Ajax: {endpoint}")
        raw_response = await self.request(user_email, "GET", endpoint)
        
        if not isinstance(raw_response, list):
            logger.warning(f"Unexpected response type for devices: {type(raw_response)}")
            return []
            
        logger.info(f"Received {len(raw_response)} devices from Ajax API")
        flattened = []
        for item in raw_response:
            device_id = item.get("deviceId") or item.get("id")
            properties = item.get("properties", {})
            
            if not device_id:
                logger.warning(f"Device item missing ID: {item}")
                continue
                
            flattened_item = {
                "deviceId": device_id,
                **properties
            }
            
            if "deviceName" in item and "deviceName" not in flattened_item:
                flattened_item["deviceName"] = item["deviceName"]
            if "deviceType" in item and "deviceType" not in flattened_item:
                flattened_item["deviceType"] = item["deviceType"]
            if "online" in item and "online" not in flattened_item:
                flattened_item["online"] = item["online"]
                
            flattened.append(flattened_item)
        
        # Cache the result
        await cache.set(cache_key, flattened, settings.CACHE_TTL_DEVICES)
        return flattened

    async def get_device_details(self, user_email: str, hub_id: str, device_id: str) -> Dict[str, Any]:
        """Get details for a specific device with caching."""
        cache = await self._get_cache()
        cache_key = cache.key_device(user_email, hub_id, device_id)
        
        async def fetch():
            user_id = await self._ensure_user_id(user_email)
            return await self.request(user_email, "GET", f"/user/{user_id}/hubs/{hub_id}/devices/{device_id}")
        
        return await cache.get_or_fetch(cache_key, settings.CACHE_TTL_DEVICE_DETAIL, fetch)

    async def set_arm_state(self, user_email: str, hub_id: str, arm_state: int, group_id: Optional[str] = None) -> Dict[str, Any]:
        """Set arm state for hub or group using the correct Swagger endpoint.
        
        After successful state change, invalidates relevant caches.
        """
        user_id = await self._ensure_user_id(user_email)
        
        # Map integer state to Swagger command strings
        # 0: DISARMED, 1: ARMED, 2: NIGHT_MODE
        state_map = {
            0: "DISARM",
            1: "ARM",
            2: "NIGHT_MODE_ON"
        }
        
        command_str = state_map.get(arm_state, "ARM")
        
        # Endpoint differs if controlling a specific group (partition)
        if group_id:
            endpoint = f"/user/{user_id}/hubs/{hub_id}/groups/{group_id}/commands/arming"
        else:
            endpoint = f"/user/{user_id}/hubs/{hub_id}/commands/arming"
            
        payload = {
            "command": command_str,
            "ignoreProblems": True
        }
        
        # Execute the command
        result = await self.request(user_email, "PUT", endpoint, json=payload)
        
        # Invalidate cache after successful state change
        try:
            cache = await self._get_cache()
            # Invalidate hub detail (contains state)
            await cache.invalidate(cache.key_hub(user_email, hub_id))
            # Invalidate hub list (contains state summary)
            await cache.invalidate(cache.key_hubs(user_email))
            logger.info(f"Cache invalidated for hub {hub_id} after arm state change")
        except Exception as e:
            logger.warning(f"Failed to invalidate cache after arm state change: {e}")
        
        return result

