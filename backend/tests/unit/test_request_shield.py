import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_request_shield_blocks_malicious_php():
    """Test that .php extensions are blocked with 403."""
    response = client.get("/index.php")
    assert response.status_code == 403
    assert response.json() == {"detail": "Forbidden: Malicious activity detected."}

def test_request_shield_blocks_sensitive_env():
    """Test that access to .env is blocked."""
    response = client.get("/config/.env")
    assert response.status_code == 403
    assert response.json() == {"detail": "Forbidden: Malicious activity detected."}

def test_request_shield_blocks_path_traversal():
    """Test that path traversal attempts are blocked."""
    response = client.get("/static/../../etc/passwd")
    assert response.status_code == 403
    assert response.json() == {"detail": "Forbidden: Malicious activity detected."}

def test_request_shield_allows_normal_paths():
    """Test that normal API paths are still allowed (assuming they exist or return 404/401, not 403)."""
    response = client.get("/health")
    # Health check should return 200, not be blocked by shield
    assert response.status_code == 200

def test_request_shield_ignore_case():
    """Test that blocking is case insensitive."""
    response = client.get("/ADMIN.PHP")
    assert response.status_code == 403
