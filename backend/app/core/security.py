import datetime
from datetime import datetime as dt_datetime, timedelta, timezone
from typing import Optional, Any, Union
import jwt # PyJWT
import bcrypt
from backend.app.core.config import settings

ALGORITHM = settings.ALGORITHM
SECRET_KEY = settings.SECRET_KEY.get_secret_value()
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a bcrypt hash.
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), 
        hashed_password.encode("utf-8")
    )

def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    """
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def _create_token(
    subject: Union[str, Any], 
    expires_delta: timedelta,
    token_type: str,
    jti: Optional[str] = None,
    uah: Optional[str] = None,
    uip: Optional[str] = None
) -> str:
    expire = dt_datetime.now(timezone.utc) + expires_delta
    to_encode = {
        "exp": expire, 
        "sub": str(subject),
        "type": token_type
    }
    if jti:
        to_encode["jti"] = jti
    if uah:
        to_encode["uah"] = uah
    if uip:
        to_encode["uip"] = uip
        
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_access_token(
    subject: Union[str, Any], 
    jti: Optional[str] = None,
    uah: Optional[str] = None,
    uip: Optional[str] = None
) -> str:
    expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return _create_token(subject, expires_delta, "access", jti, uah, uip)

def create_refresh_token(
    subject: Union[str, Any], 
    jti: Optional[str] = None
) -> str:
    expires_delta = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    return _create_token(subject, expires_delta, "refresh", jti)
