
# server/src/core/config.py
from pydantic import Field
from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    """Cấu hình tổng thể ứng dụng"""
    
    # App settings
    app_name: str = "Telegram Voice Reply Server"
    debug: bool = Field(False, description="Chế độ debug")
    host: str = Field("0.0.0.0", description="Host bind")
    port: int = Field(8000, description="Port bind")
    
    # Telegram settings
    telegram_api_id: int = Field(..., description="Telegram API ID")
    telegram_api_hash: str = Field(..., description="Telegram API Hash")
    telegram_phone: str = Field(..., description="Số điện thoại Telegram")
    telegram_session_string: str = Field(None, description="Session string (production)")
    
    # Database (optional)
    database_url: str = Field(None, description="Database connection string")
    
    # Security
    secret_key: str = Field(..., description="Secret key cho JWT")
    
    # CORS
    allowed_origins: list = Field(
        default=["*"], 
        description="Danh sách domain được phép CORS"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()