import asyncio
import os
from unittest.mock import MagicMock
from backend.app.modules.ajax.service import AjaxClient, AjaxAuthError
from backend.app.core.config import settings

async def test_ajax_client_url_construction():
    print("--- Testing AjaxClient URL Construction ---")
    print(f"Settings Base URL: {settings.AJAX_API_BASE_URL}")
    
    # We don't need a real redis for this test if we don't call save_session_data
    client = AjaxClient(redis_client=MagicMock())
    
    # Check the base_url of the internal httpx client
    print(f"Internal httpx base_url: {client.client.base_url}")
    
    # We will try to login. Even with fake credentials, we want to see the 404 vs 401
    try:
        print("\nAttempting login with 'AjaxClient.login_with_credentials'...")
        # We temporarily mock settings to use the ones from .env for real test
        # but the logic is what matters
        await client.login_with_credentials("fake@example.com", "fake_password")
    except AjaxAuthError as e:
        print(f"Caught expected AjaxAuthError: {e}")
    except Exception as e:
        print(f"Caught unexpected Exception: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_ajax_client_url_construction())
