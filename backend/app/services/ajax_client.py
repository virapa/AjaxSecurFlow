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
        """
        Lazy initialization of Redis client.
        In a real Dependency Injection scenario, this should probably be injected,
        but for a Singleton service, lazy loading the redis connection is acceptable.
        """
        if not self.redis:
            self.redis = redis.from_url(
                str(settings.REDIS_URL), 
                encoding="utf-8", 
                decode_responses=True
            )
        return self.redis

    async def _get_session_token(self) -> Optional[str]:
        """
        Retrieve session token from Redis.
        """
        redis_client = await self._get_redis()
        token = await redis_client.get("ajax_session_token")
        return token

    async def _save_session_token(self, token: str, expires_in: int = 3600):
        """
        Save session token to Redis.
        """
        redis_client = await self._get_redis()
        # Set expiry slightly less than actual to avoid race conditions
        await redis_client.set("ajax_session_token", token, ex=expires_in - 60)

    @retry(
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def login(self) -> str:
        """
        Perform login to Ajax Systems to get a new session token.
        Authenticates using credentials from settings.
        """
        logger.info("Attempting to login to Ajax Systems API...")
        
        # Access secret values properly
        payload = {
            "login": settings.AJAX_LOGIN,
            "password": settings.AJAX_PASSWORD.get_secret_value(),
            "user_api_key": settings.AJAX_API_KEY.get_secret_value()
        }
        
        try:
            response = await self.client.post("/login", json=payload)
            response.raise_for_status()
            data = response.json()
            
            token = data.get("session_token") or data.get("token")
            
            if not token:
                raise AjaxAuthError("Login successful but no token found in response.")
                
            expires_in = data.get("expires_in", 3600) 
            await self._save_session_token(token, int(expires_in))
            logger.info("Successfully logged in to Ajax Systems.")
            return token
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Login failed: {e.response.text}")
            raise AjaxAuthError(f"Login failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during login: {e}")
            raise

    async def request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make an authenticated request to Ajax API.
        Auto-refreshes token on 401.
        """
        token = await self._get_session_token()
        
        if not token:
            token = await self.login()

        headers = kwargs.get("headers", {})
        headers["X-Session-Token"] = token
        kwargs["headers"] = headers

        try:
            response = await self.client.request(method, endpoint, **kwargs)
            
            # Handle 401 specifically
            if response.status_code == 401:
                logger.warning("Token expired (401). Refreshing token and retrying...")
                token = await self.login()
                kwargs["headers"]["X-Session-Token"] = token
                response = await self.client.request(method, endpoint, **kwargs)
            
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Request to {endpoint} failed: {e.response.text}")
            raise
