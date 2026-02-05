import pytest
from unittest.mock import patch, MagicMock
from backend.app.services.email_service import send_email

@pytest.fixture
def mock_settings():
    with patch("backend.app.services.email_service.settings") as mock:
        mock.SMTP_HOST = "smtp.mock.com"
        mock.SMTP_PORT = 587
        mock.SMTP_TLS = True
        mock.SMTP_USER = "user"
        mock.SMTP_PASSWORD.get_secret_value.return_value = "password"
        mock.SMTP_FROM_NAME = "AjaxSecurFlow"
        mock.SMTP_FROM_EMAIL = "noreply@mock.com"
        yield mock

def test_send_email_success(mock_settings):
    with patch("smtplib.SMTP") as mock_smtp:
        mock_server = mock_smtp.return_value.__enter__.return_value
        
        result = send_email(
            to_email="test@user.com",
            subject="Welcome",
            body_html="<h1>Hi</h1>",
            body_text="Hi"
        )
        
        assert result is True
        assert mock_server.login.called
        assert mock_server.sendmail.called
        # Verify message construction roughly
        args, kwargs = mock_server.sendmail.call_args
        assert args[0] == "noreply@mock.com"
        assert args[1] == "test@user.com"

def test_send_email_no_config():
    with patch("backend.app.services.email_service.settings") as mock_settings:
        mock_settings.SMTP_HOST = None
        
        result = send_email("t@e.com", "S", "H")
        assert result is False

def test_send_email_exception(mock_settings):
    with patch("smtplib.SMTP") as mock_smtp:
        mock_smtp.side_effect = Exception("SMTP Error")
        
        result = send_email("t@e.com", "S", "H")
        assert result is False
