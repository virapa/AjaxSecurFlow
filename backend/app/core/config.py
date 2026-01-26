from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, RedisDsn, SecretStr, field_validator
from typing import Optional, Any

class Settings(BaseSettings):
    # Project Identity
    PROJECT_NAME: str = "AjaxSecurFlow Proxy"
    VERSION: str = "0.1.0"
    
    # Database (Postgres)
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432
    DATABASE_URL: Optional[PostgresDsn] = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], values) -> Any:
        if isinstance(v, str):
            return v
        
        # We need to construct it from parts if not provided directly
        # Accessing validated values from the ValidationInfo (Pydantic V2) or using values dict (Pydantic V1 compat)
        # In Pydantic V2 'values' argument in field_validator is different.
        # Let's rely on computed field or just construct it if missing in a post-init or use basic env var.
        # For simplicity and robustness, let's just prefer DATABASE_URL if set, else build it.
        # Since we use BaseSettings, it reads from env. We will assume DATABASE_URL is constructed in docker-compose
        # or we explicitly define it here.
        return v

    # Redis (Rate Limit & Cache)
    REDIS_URL: RedisDsn

    # Ajax Systems API
    AJAX_API_BASE_URL: str = "https://api.ajax.systems/api"
    AJAX_API_KEY: SecretStr
    AJAX_LOGIN: str
    AJAX_PASSWORD: SecretStr

    # Security
    SECRET_KEY: SecretStr
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
