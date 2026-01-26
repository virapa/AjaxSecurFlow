import os
import pytest

# Set environment variables for testing before other modules are loaded
os.environ["POSTGRES_USER"] = "test_user"
os.environ["POSTGRES_PASSWORD"] = "test_pass"
os.environ["POSTGRES_DB"] = "test_db"
os.environ["POSTGRES_HOST"] = "localhost"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["AJAX_API_KEY"] = "test_key"
os.environ["AJAX_LOGIN"] = "test_login"
os.environ["AJAX_PASSWORD"] = "test_password"
os.environ["SECRET_KEY"] = "supersecretkeyformocking12345"
