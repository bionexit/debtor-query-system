from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "Debtor Query System"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "sqlite:///./debtor.db"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production-use-strong-random-value"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # SMS Gateway
    SMS_GATEWAY_URL: str = "http://localhost:8001"
    SMS_GATEWAY_API_KEY: str = "mock-sms-api-key"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Captcha
    CAPTCHA_EXPIRE_SECONDS: int = 300
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15
    
    # H5 API
    H5_TOKEN_EXPIRE_DAYS: int = 7
    H5_DAILY_QUERY_LIMIT: int = 100
    
    # AES Encryption Key (32 bytes for AES-256)
    AES_KEY: str = "your-32-byte-aes-encryption-key-h"

    class Config:
        env_file = ".env"


settings = Settings()
