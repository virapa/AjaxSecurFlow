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

    async def _get_ajax_user_id(self) -> Optional[str]:
        """
        Retrieve the cached Ajax userId from Redis.

        Returns:
            Optional[str]: The userId if found, None otherwise.
        """
        redis_client = await self._get_redis()
        return await redis_client.get("ajax_user_id")

    async def _get_session_token(self) -> Optional[str]:
        """
        Retrieve the cached Ajax session token from Redis.

        Returns:
            Optional[str]: The session token if found, None otherwise.
        """
        redis_client = await self._get_redis()
        return await redis_client.get("ajax_session_token")

    async def _save_session_data(self, token: str, user_id: str, expires_in: int = 3600) -> None:
        """
        Save session token and userId to Redis with an expiration.

        Args:
            token: The session token to save.
            user_id: The Ajax userId associated with the session.
            expires_in: Expiration time in seconds (default: 3600).
        """
        redis_client = await self._get_redis()
        # Subtracting 60 seconds as a safety buffer for expiration
        await redis_client.set("ajax_session_token", token, ex=expires_in - 60)
        await redis_client.set("ajax_user_id", user_id, ex=expires_in - 60)

    @retry(
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def login(self) -> str:
        """
        Authenticate with Ajax Systems to obtain a new session token.
        Uses SHA256 hashing for the password as required by the API.

        Returns:
            str: The newly obtained session token.

        Raises:
            AjaxAuthError: If authentication fails or required data is missing.
        """
        logger.info("Attempting to login to Ajax Systems API...")
        
        import hashlib
        
        # 1. Prepare password hash
        password_raw = settings.AJAX_PASSWORD.get_secret_value()
        sha256_hash = hashlib.sha256()
        sha256_hash.update(password_raw.encode('utf-8'))
        password_hash = sha256_hash.hexdigest()
        
        # 2. Build payload and headers
        payload = {
            "login": settings.AJAX_LOGIN,
            "passwordHash": password_hash,
            "userRole": "USER" 
        }
        
        headers = {
            "X-Api-Key": settings.AJAX_API_KEY.get_secret_value(),
            "Content-Type": "application/json",
            "accept": "application/json"
        }
        
        try:
            logger.info("Sending Login Request to Ajax Systems...")
            response = await self.client.post("/login", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            token = data.get("sessionToken")
            user_id = data.get("userId")
            
            if not token or not user_id:
                logger.error(f"Incomplete login response data: {data}")
                raise AjaxAuthError("Login successful but sessionToken or userId is missing from response.")
                
            expires_in = data.get("expires_in", 3600) 
            await self._save_session_data(token, user_id, int(expires_in))
            logger.info(f"Successfully authenticated. Ajax User ID: {user_id}")
            return token
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Ajax authentication failed (Status {e.response.status_code}): {e.response.text}")
            raise AjaxAuthError(f"Authentication failed: {e.response.text}")
        except Exception as e:
            logger.error(f"Unexpected error during Ajax login: {e}")
            raise

    async def request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Execute an authenticated HTTP request to the Ajax API.
        Automatically handles token refresh on 401 Unauthorized errors.

        Args:
            method: HTTP method (GET, POST, etc.).
            endpoint: API endpoint path.
            **kwargs: Additional arguments for httpx client (json, params, headers, etc.).

        Returns:
            Dict[str, Any]: The parsed JSON response.

        Raises:
            httpx.HTTPStatusError: If the response indicates an error other than 401.
        """
        token = await self._get_session_token()
        
        if not token:
            token = await self.login()

        # Inject mandatory headers
        headers = kwargs.get("headers", {})
        headers["X-Api-Key"] = settings.AJAX_API_KEY.get_secret_value()
        headers["X-Session-Token"] = token
        headers["accept"] = "application/json"
        kwargs["headers"] = headers

        try:
            response = await self.client.request(method, endpoint, **kwargs)
            
            # Handle token expiration
            if response.status_code == 401:
                logger.warning("Session token expired or invalid (401). Retrying authentication...")
                token = await self.login()
                kwargs["headers"]["X-Session-Token"] = token
                response = await self.client.request(method, endpoint, **kwargs)
            
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"API request to {endpoint} failed: {e.response.text}")
            raise

    async def _ensure_user_id(self) -> str:
        """
        Ensure that the Ajax userId is available, performing a login if necessary.

        Returns:
            str: The Ajax userId.
        """
        user_id = await self._get_ajax_user_id()
        if not user_id:
            await self.login()
            user_id = await self._get_ajax_user_id()
            if not user_id:
                raise AjaxAuthError("Failed to obtain userId after login.")
        return user_id

    async def get_hubs(self) -> Dict[str, Any]:
        """
        Fetch the list of hubs associated with the authenticated user.

        Returns:
            Dict[str, Any]: Response containing the list of hubs.
        """
        user_id = await self._ensure_user_id()
        return await self.request("GET", f"/user/{user_id}/hubs")

    async def get_hub_details(self, hub_id: str) -> Dict[str, Any]:
        """
        Retrieve detailed information about a specific hub.

        Args:
            hub_id: The unique identifier of the hub.

        Returns:
            Dict[str, Any]: Detailed hub information.
        """
        user_id = await self._ensure_user_id()
        return await self.request("GET", f"/user/{user_id}/hubs/{hub_id}")

    async def get_hub_logs(self, hub_id: str, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """
        Fetch event logs for a specific hub.

        Args:
            hub_id: The unique identifier of the hub.
            limit: Maximum number of log entries to retrieve.
            offset: Starting point for pagination.

        Returns:
            Dict[str, Any]: A list of event logs and pagination metadata.
        """
        user_id = await self._ensure_user_id()
        params = {"limit": limit, "offset": offset}
        return await self.request("GET", f"/user/{user_id}/hubs/{hub_id}/logs", params=params)

    async def get_hub_groups(self, hub_id: str) -> Dict[str, Any]:
        """
        Retrieve the list of security groups configured on a hub.

        Args:
            hub_id: The unique identifier of the hub.

        Returns:
            Dict[str, Any]: List of groups and their statuses.
        """
        user_id = await self._ensure_user_id()
        return await self.request("GET", f"/user/{user_id}/hubs/{hub_id}/groups")

    async def get_hub_devices(self, hub_id: str) -> Dict[str, Any]:
        """
        Fetch all devices linked to a specific hub, including enriched state information.

        Args:
            hub_id: The unique identifier of the hub.

        Returns:
            Dict[str, Any]: List of devices with detailed properties.
        """
        user_id = await self._ensure_user_id()
        return await self.request("GET", f"/user/{user_id}/hubs/{hub_id}/devices?enrich=true")

    async def set_arm_state(self, hub_id: str, arm_state: int, group_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Send an arming or disarming command to a hub or specific group.

        Args:
            hub_id: Unique identifier of the hub.
            arm_state: Target state (1: ARM, 0: DISARM, 2: NIGHT).
            group_id: Optional group/partition ID.

        Returns:
            Dict[str, Any]: Response from the API.
        """
        user_id = await self._ensure_user_id()
        payload = {"armState": arm_state}
        if group_id:
            payload["groupId"] = group_id
            
        return await self.request(
            "POST", 
            f"/user/{user_id}/hubs/{hub_id}/commands/set-arm-state", 
            json=payload
        )

    async def arm(self, hub_id: str, group_id: Optional[str] = None) -> Dict[str, Any]:
        """Convenience method for Full Arming (Armado Total)."""
        return await self.set_arm_state(hub_id, 1, group_id)

    async def disarm(self, hub_id: str, group_id: Optional[str] = None) -> Dict[str, Any]:
        """Convenience method for Disarming (Desarmado)."""
        return await self.set_arm_state(hub_id, 0, group_id)

    async def night_mode(self, hub_id: str) -> Dict[str, Any]:
        """Convenience method for Night Mode (Armado Parcial)."""
        return await self.set_arm_state(hub_id, 2)
