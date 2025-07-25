# server/src/telegram/client.py
import asyncio
import logging
from typing import Optional
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError, SessionPasswordNeededError
from .config import telegram_settings

logger = logging.getLogger(__name__)

class TelegramClientManager:
    """Quản lý Telegram client singleton"""
    
    def __init__(self):
        self._client: Optional[TelegramClient] = None
        self._lock = asyncio.Lock()
        self._connected = False
        
    @property
    def client(self) -> Optional[TelegramClient]:
        return self._client
        
    @property 
    def is_connected(self) -> bool:
        return self._connected and self._client and self._client.is_connected()
        
    async def initialize(self) -> TelegramClient:
        """Khởi tạo và kết nối Telegram client"""
        if self._client is None:
            async with self._lock:
                if self._client is None:
                    await self._create_client()
        return self._client
        
    async def _create_client(self):
        """Tạo client và kết nối"""
        try:
            # Chọn session type
            if telegram_settings.session_string:
                logger.info("Sử dụng StringSession từ biến môi trường")
                session = StringSession(telegram_settings.session_string)
            else:
                session_file = f"{telegram_settings.session_dir}/session"
                logger.info(f"Sử dụng file session: {session_file}")
                session = session_file
                
            # Tạo client
            self._client = TelegramClient(
                session,
                telegram_settings.api_id,
                telegram_settings.api_hash,
                flood_sleep_threshold=telegram_settings.flood_sleep_threshold
            )
            
            # Kết nối
            await self._client.start(phone=telegram_settings.phone)
            self._connected = True
            
            # Lấy thông tin user để xác nhận
            me = await self._client.get_me()
            logger.info(f"Đã kết nối Telegram: {me.first_name} (@{me.username})")
            
        except SessionPasswordNeededError:
            logger.error("Tài khoản có bật 2FA. Cần nhập password!")
            raise
        except Exception as e:
            logger.error(f"Lỗi kết nối Telegram: {e}")
            raise
            
    async def disconnect(self):
        """Ngắt kết nối client"""
        if self._client and self._client.is_connected():
            await self._client.disconnect()
            self._connected = False
            logger.info("Đã ngắt kết nối Telegram")
            
    async def send_message_safe(self, chat_id: int, message: str, max_retries: int = 3):
        """Gửi tin nhắn với retry logic"""
        if not self.is_connected:
            raise Exception("Telegram client chưa kết nối")
            
        for attempt in range(max_retries):
            try:
                return await self._client.send_message(chat_id, message)
            except FloodWaitError as e:
                if attempt == max_retries - 1:
                    raise
                wait_time = min(e.seconds, 300)  # Tối đa 5 phút
                logger.warning(f"FloodWait {e.seconds}s, chờ {wait_time}s...")
                await asyncio.sleep(wait_time)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"Lỗi gửi tin (thử {attempt+1}/{max_retries}): {e}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

# Singleton instance
telegram_manager = TelegramClientManager()