# server/src/telegram/client.py
import asyncio
import logging
from typing import Optional
from pathlib import Path
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError, SessionPasswordNeededError

logger = logging.getLogger(__name__)

class TelegramClientManager:
    """Telegram client singleton manager"""
    
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
        """Initialize and connect Telegram client"""
        if self._client is None:
            async with self._lock:
                if self._client is None:
                    await self._create_client()
        return self._client
        
    async def _create_client(self):
        """Create client and connect"""
        try:
            # Import settings here to avoid circular imports
            from src.core.config import settings
            
            # Validate credentials
            if not settings.telegram_api_id or not settings.telegram_api_hash:
                raise ValueError("Missing Telegram API credentials")
            
            # Choose session type
            if settings.telegram_session_string:
                logger.info("Using StringSession from environment")
                session = StringSession(settings.telegram_session_string)
            else:
                # Create sessions directory if it doesn't exist
                session_dir = Path("server/sessions")
                session_dir.mkdir(parents=True, exist_ok=True)
                
                session_file = session_dir / "session"
                logger.info(f"Using file session: {session_file}")
                session = str(session_file)
                
            # Create client
            self._client = TelegramClient(
                session,
                settings.telegram_api_id,
                settings.telegram_api_hash,
                flood_sleep_threshold=60,
                auto_reconnect=True,
                connection_retries=5,
                retry_delay=1,
                timeout=30
            )
            
            # Connect with timeout
            logger.info("Connecting to Telegram...")
            await asyncio.wait_for(self._client.connect(), timeout=30)
            
            # Check if authorized
            if not await self._client.is_user_authorized():
                if settings.telegram_session_string:
                    logger.error("Session string is invalid or expired!")
                    raise ValueError("Invalid session string")
                else:
                    logger.error("Not authorized! Need to login with phone number.")
                    raise ValueError("Not authorized")
            
            self._connected = True
            
            # Get user info to confirm
            me = await self._client.get_me()
            logger.info(f"✅ Connected to Telegram as: {me.first_name} (@{me.username}) - ID: {me.id}")
            
        except asyncio.TimeoutError:
            logger.error("Telegram connection timeout!")
            raise
        except SessionPasswordNeededError:
            logger.error("Account has 2FA enabled. Password required!")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to Telegram: {e}")
            self._connected = False
            raise
            
    async def disconnect(self):
        """Disconnect client"""
        if self._client and self._client.is_connected():
            await self._client.disconnect()
            self._connected = False
            logger.info("Disconnected from Telegram")
            
    async def send_message_safe(self, chat_id: int, message: str, max_retries: int = 3):
        """Send message with retry logic"""
        if not self.is_connected:
            raise Exception("Telegram client not connected")
            
        for attempt in range(max_retries):
            try:
                return await self._client.send_message(chat_id, message)
            except FloodWaitError as e:
                if attempt == max_retries - 1:
                    raise
                wait_time = min(e.seconds, 300)  # Max 5 minutes
                logger.warning(f"FloodWait {e.seconds}s, waiting {wait_time}s...")
                await asyncio.sleep(wait_time)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"Send error (attempt {attempt+1}/{max_retries}): {e}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

# Singleton instance
telegram_manager = TelegramClientManager()
