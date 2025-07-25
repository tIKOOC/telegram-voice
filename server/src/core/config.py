# server/src/core/config.py
import os
from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application configuration"""
    
    # App settings
    app_name: str = "Telegram Voice Reply Server"
    debug: bool = Field(default=False)
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    
    # Telegram settings - Make optional for health check to work
    telegram_api_id: Optional[int] = Field(default=None)
    telegram_api_hash: Optional[str] = Field(default=None)
    telegram_phone: Optional[str] = Field(default=None)
    telegram_session_string: Optional[str] = Field(default=None)
    
    # Security
    secret_key: str = Field(default="default-secret-key-change-in-production")
    
    # CORS
    allowed_origins: List[str] = Field(default=["*"])
    
    @validator('telegram_api_id', pre=True)
    def validate_api_id(cls, v):
        if v is None or v == '':
            return None
        try:
            return int(v)
        except ValueError:
            raise ValueError(f"Invalid TELEGRAM_API_ID: {v}")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        
        # Allow environment variables to override
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str):
            if field_name == 'allowed_origins':
                return [x.strip() for x in raw_val.split(',')]
            return raw_val

# Create settings instance
settings = Settings()
