from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class Token(BaseModel):
    access_token: str = Field(..., description="JWT access token for API requests (short-lived)")
    refresh_token: str = Field(..., description="JWT refresh token to obtain new access tokens (long-lived)")
    token_type: str = Field("bearer", description="Token type, always 'bearer'")

class TokenData(BaseModel):
    email: Optional[str] = None

class TokenRefreshRequest(BaseModel):
    refresh_token: str = Field(..., description="The long-lived refresh token received during login")

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class ErrorMessage(BaseModel):
    detail: str
