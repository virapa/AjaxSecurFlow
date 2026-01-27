import httpx
import redis.asyncio as redis
import logging
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from backend.app.core.config import settings

# Logging
logger = logging.getLogger(__name__)

class AjaxAuthError(Exception):
    """Custom exception for Ajax Authentication failures."""
    pass

class AjaxClient:
    """
    Async Client for Ajax Systems API.
    Handles Authentication (Session Token) with Redis Caching and Automatic Renewal.
    Singleton pattern to ensure shared HTTP connection pool.
    """
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AjaxClient, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.redis: Optional[redis.Redis] = None
            # Initialize HTTP client with base URL from settings
            self.client = httpx.AsyncClient(
                base_url=settings.AJAX_API_BASE_URL, 
                timeout=10.0
            )
            self.initialized = True

    async def _get_redis(self) -> redis.Redis:
        if not self.redis:
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
        """
        Retrieve the cached Ajax session token for a specific user.

        Args:
            user_email: The email of the user as unique identifier.

        Returns:
            Optional[str]: The session token if found in cache.
        """
        redis_client = await self._get_redis()
        return await redis_client.get(f"ajax_user:{user_email}:token")

    async def _save_session_data(self, user_email: str, token: str, user_id: str, expires_in: int = 3600) -> None:
        """
        Save session token and userId to Redis for a specific user.

        Args:
            user_email: The user's email.
            token: The Ajax session token.
            user_id: The Ajax user ID.
            expires_in: TTL for the cache (in seconds).
        """
        redis_client = await self._get_redis()
        # Safety buffer of 60 seconds
        await redis_client.set(f"ajax_user:{user_email}:token", token, ex=expires_in - 60)
        await redis_client.set(f"ajax_user:{user_email}:id", user_id, ex=expires_in - 60)

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
            
            if not token or not user_id:
                raise AjaxAuthError("Login successful but missing session data.")
                
            expires_in = data.get("expires_in", 3600) 
            await self._save_session_data(email, token, user_id, int(expires_in))
            return data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Ajax validation failed for {email}: {e.response.text}")
            raise AjaxAuthError("Invalid Ajax credentials.")
        except Exception as e:
            logger.error(f"Error during Ajax credential validation: {e}")
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
            raise AjaxAuthError("Session expired. Please log in again.")

        headers = kwargs.get("headers", {})
        headers["X-Api-Key"] = settings.AJAX_API_KEY.get_secret_value()
        headers["X-Session-Token"] = token
        headers["accept"] = "application/json"
        kwargs["headers"] = headers

        try:
            response = await self.client.request(method, endpoint, **kwargs)
            
            if response.status_code == 401:
                raise AjaxAuthError("Ajax session expired.")
            
            response.raise_for_status()
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

    async def get_hubs(self, user_email: str) -> Dict[str, Any]:
        """Get hubs for user."""
        user_id = await self._ensure_user_id(user_email)
        return await self.request(user_email, "GET", f"/user/{user_id}/hubs")

    async def get_hub_details(self, user_email: str, hub_id: str) -> Dict[str, Any]:
        """Get hub detail."""
        user_id = await self._ensure_user_id(user_email)
        return await self.request(user_email, "GET", f"/user/{user_id}/hubs/{hub_id}")

    async def get_hub_logs(self, user_email: str, hub_id: str, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Get hub event logs."""
        user_id = await self._ensure_user_id(user_email)
        params = {"limit": limit, "offset": offset}
        return await self.request(user_email, "GET", f"/user/{user_id}/hubs/{hub_id}/logs", params=params)

    async def get_hub_groups(self, user_email: str, hub_id: str) -> Dict[str, Any]:
        """Get hub security groups."""
        user_id = await self._ensure_user_id(user_email)
        return await self.request(user_email, "GET", f"/user/{user_id}/hubs/{hub_id}/groups")

    async def get_hub_devices(self, user_email: str, hub_id: str) -> Dict[str, Any]:
        """Get hub devices with enriched state."""
        user_id = await self._ensure_user_id(user_email)
        return await self.request(user_email, "GET", f"/user/{user_id}/hubs/{hub_id}/devices?enrich=true")

    async def set_arm_state(self, user_email: str, hub_id: str, arm_state: int, group_id: Optional[str] = None) -> Dict[str, Any]:
        """Set arm state for hub or group."""
        user_id = await self._ensure_user_id(user_email)
        payload = {"armState": arm_state}
        if group_id:
            payload["groupId"] = group_id
        return await self.request(user_email, "POST", f"/user/{user_id}/hubs/{hub_id}/commands/set-arm-state", json=payload)
