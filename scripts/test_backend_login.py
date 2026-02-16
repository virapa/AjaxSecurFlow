import httpx
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://localhost:8000/api/v1"
USERNAME = os.getenv("AJAX_LOGIN")
PASSWORD = os.getenv("AJAX_PASSWORD")

async def test_backend_login():
    print(f"Testing Backend Login for {USERNAME}...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(
                f"{BASE_URL}/auth/token",
                json={"username": USERNAME, "password": PASSWORD}
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 200:
                print("✅ Backend login successful!")
                print(f"Cookies: {response.cookies.keys()}")
            else:
                print("❌ Backend login failed.")
        except Exception as e:
            print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_backend_login())
