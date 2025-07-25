# server/src/core/config.py
import os
from typing import List, Optional, Union
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
    
    # CORS - Handle as string or list
    allowed_origins: Union[List[str], str] = Field(default=["*"])
    
    @validator('telegram_api_id', pre=True)
    def validate_api_id(cls, v):
        if v is None or v == '':
            return None
        try:
            return int(v)
        except ValueError:
            raise ValueError(f"Invalid TELEGRAM_API_ID: {v}")
    
    @validator('allowed_origins', pre=True)
    def parse_allowed_origins(cls, v):
        # If it's already a list, return it
        if isinstance(v, list):
            return v
        # If it's a string, handle different formats
        if isinstance(v, str):
            # Handle empty string
            if not v or v.strip() == '':
                return ["*"]
            # Handle asterisk
            if v.strip() == '*' or v.strip() == '["*"]' or v.strip() == '[]':
                return ["*"]
            # Try to parse as JSON array
            import json
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
                return [str(parsed)]
            except json.JSONDecodeError:
                # Not JSON, treat as comma-separated values
                return [origin.strip() for origin in v.split(',') if origin.strip()]
        return ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Create settings instance
settings = Settings()
