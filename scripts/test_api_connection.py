import httpx
import sys

BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "admin@example.com"
PASSWORD = "changethis"

def test_connection():
    # 1. Authenticate
    print(f"Authenticating as {USERNAME}...")
    try:
        auth_response = httpx.post(
            f"{BASE_URL}/auth/token",
            data={"username": USERNAME, "password": PASSWORD}
        )
        auth_response.raise_for_status()
        token = auth_response.json()["access_token"]
        print("✅ Authentication successful. Token received.")
    except Exception as e:
        print(f"❌ Authentication Failed: {e}")
        if 'auth_response' in locals():
            print(f"Response: {auth_response.text}")
        return

    # 2. Get Hubs (Test Ajax Proxy)
    print("\nRequesting Hubs from Ajax Proxy...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        hubs_response = httpx.get(f"{BASE_URL}/ajax/hubs", headers=headers, timeout=30.0)
        
        if hubs_response.status_code == 200:
            print("✅ Hubs request successful.")
            hubs = hubs_response.json()
            print(f"Found {len(hubs)} hubs.")
            print(f"Data: {hubs}")
        else:
            print(f"❌ Hubs request failed with status {hubs_response.status_code}")
            print(f"Response: {hubs_response.text}")

    except Exception as e:
        print(f"❌ Request Error: {e}")

if __name__ == "__main__":
    test_connection()
