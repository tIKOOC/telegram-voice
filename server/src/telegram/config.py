# server/src/telegram/config.py  
from pydantic_settings import BaseSettings
from pydantic import Field

class TelegramSettings(BaseSettings):
    """Cấu hình riêng cho Telegram"""
    
    api_id: int = Field(..., env="TELEGRAM_API_ID")
    api_hash: str = Field(..., env="TELEGRAM_API_HASH") 
    phone: str = Field(..., env="TELEGRAM_PHONE")
    session_string: str = Field(None, env="TELEGRAM_SESSION_STRING")
    session_dir: str = Field("./sessions", env="TELEGRAM_SESSION_DIR")
    
    # Rate limiting
    max_requests_per_second: int = Field(20, description="Giới hạn request/giây")
    flood_sleep_threshold: int = Field(60, description="Ngưỡng flood sleep")
    
    class Config:
        env_file = ".env"
        env_prefix = "TELEGRAM_"

telegram_settings = TelegramSettings()