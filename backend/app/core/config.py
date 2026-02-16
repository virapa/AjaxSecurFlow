from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, RedisDsn, SecretStr, field_validator
from typing import Optional, Any

class Settings(BaseSettings):
    # Project Identity
    PROJECT_NAME: str = "AjaxSecurFlow Proxy"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENABLE_DEVELOPER_MODE: bool = False # Bypass Stripe for dev/test
    
    # Database (Postgres)
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432
    DATABASE_URL: Optional[str] = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Any) -> Any:
        if isinstance(v, str) and v.strip() == "":
            return None
        return v
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        if self.DATABASE_URL and self.DATABASE_URL.strip():
            return self.DATABASE_URL
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Redis (Rate Limit & Cache)
    REDIS_URL: str

    # Ajax Systems API
    AJAX_API_BASE_URL: str = "https://api.ajax.systems/api/"
    AJAX_API_KEY: SecretStr
    #Solo para dev y test
    AJAX_LOGIN: Optional[str] = None
    AJAX_PASSWORD: Optional[SecretStr] = None
    
    # Stripe (SaaS Billing)
    STRIPE_SECRET_KEY: Optional[SecretStr] = None
    STRIPE_PUBLIC_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[SecretStr] = None
    
    # Stripe Price IDs for the 4 tiers
    STRIPE_PRICE_ID_BASIC: Optional[str] = None
    STRIPE_PRICE_ID_PRO: Optional[str] = None
    STRIPE_PRICE_ID_PREMIUM: Optional[str] = None
    
    # Celery (Task Queue)
    CELERY_BROKER_URL: Optional[str] = None # Defaults to Redis
    CELERY_RESULT_BACKEND: Optional[str] = None

    # Security
    SECRET_KEY: SecretStr
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    # Cookie Security
    COOKIE_SECURE: bool = True     # Set to True for HTTPS (Nginx Proxy Manager)
    COOKIE_SAMESITE: str = "lax"
    COOKIE_DOMAIN: Optional[str] = None
    # Admin Security (Ghost Admin + Master Key)
    ADMIN_EMAILS: list[str] = [] # Emails authorized for admin actions
    ADMIN_SECRET_KEY: Optional[SecretStr] = None # Physical secondary key for hazardous actions

    # CORS
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Email / SMTP (Point 2)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[SecretStr] = None
    SMTP_FROM_EMAIL: Optional[str] = None
    SMTP_FROM_NAME: Optional[str] = None
    SMTP_TLS: bool = True

    # Cache TTL Settings (in seconds) - Adjustable via environment variables
    CACHE_TTL_HUBS: int = 1800           # 30 minutes - Hub list rarely changes
    CACHE_TTL_HUB_DETAIL: int = 120      # 2 minutes - Hub state (armed/disarmed)
    CACHE_TTL_DEVICES: int = 600         # 10 minutes - Device list
    CACHE_TTL_DEVICE_DETAIL: int = 30    # 30 seconds - Device telemetry
    CACHE_TTL_ROOMS: int = 600           # 10 minutes - Rooms rarely change
    CACHE_TTL_GROUPS: int = 600          # 10 minutes - Groups rarely change

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
