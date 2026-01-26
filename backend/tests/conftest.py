import os
import pytest

# Set environment variables for testing before other modules are loaded
# MOCKING:
# For UNIT tests, these values don't matter as we mock the DB.
# For INTEGRATION tests, we need real values if we are hitting the DB.
# However, conftest runs for BOTH.
# We should probably separate integration tests or use a conditional fixture.
# But for now, let's use the Values that MATCH the docker-compose localhost setup.
os.environ["POSTGRES_USER"] = "postgres"
os.environ["POSTGRES_PASSWORD"] = "postgres"
os.environ["POSTGRES_DB"] = "ajax_proxy"
os.environ["POSTGRES_HOST"] = "localhost" # Connect from host to container port mapped to localhost
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/ajax_proxy"

os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["AJAX_API_KEY"] = "test_key"
os.environ["AJAX_LOGIN"] = "test_login"
os.environ["AJAX_PASSWORD"] = "test_password"
os.environ["SECRET_KEY"] = "supersecretkeyformocking12345"
