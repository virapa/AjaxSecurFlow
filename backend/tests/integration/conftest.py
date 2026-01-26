import pytest
import pytest_asyncio
import httpx
from httpx import AsyncClient
from backend.app.main import app

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
