# server/src/telegram/handlers.py
import logging
from telethon import events
from telethon.tl.types import PeerUser
from api.websocket import websocket_manager
from .schemas import TelegramMessage

logger = logging.getLogger(__name__)

async def register_handlers(client):
    """Đăng ký các event handlers cho Telegram client"""
    
    @client.on(events.NewMessage)
    async def handle_new_message(event):
        """Xử lý tin nhắn mới từ Telegram"""
        try:
            # Chỉ xử lý tin nhắn riêng tư (không phải group/channel)
            if not event.is_private:
                return
                
            # Bỏ qua tin nhắn từ chính mình
            if event.out:
                return
                
            # Lấy thông tin người gửi
            sender = await event.get_sender()
            if not sender:
                logger.warning("Không thể lấy thông tin sender")
                return
                
            # Tạo tên hiển thị
            sender_name = []
            if sender.first_name:
                sender_name.append(sender.first_name)
            if sender.last_name:
                sender_name.append(sender.last_name)
                
            display_name = " ".join(sender_name) if sender_name else (
                sender.username or f"User{sender.id}"
            )
            
            # Tạo message object
            message_data = TelegramMessage(
                chat_id=event.peer_id.user_id,
                sender=display_name,
                text=event.message.message or "",
                message_id=event.message.id,
                date=event.message.date
            )
            
            logger.info(f"📨 New message from {display_name}: {message_data.text[:50]}...")
            
            # Broadcast qua WebSocket
            await websocket_manager.broadcast_message(message_data.dict())
            
        except Exception as e:
            logger.error(f"Error handling new message: {e}", exc_info=True)
    
    @client.on(events.MessageEdited)
    async def handle_message_edited(event):
        """Xử lý tin nhắn được chỉnh sửa"""
        try:
            if not event.is_private or event.out:
                return
                
            sender = await event.get_sender()
            display_name = f"{sender.first_name or ''} {sender.last_name or ''}".strip() or sender.username or f"User{sender.id}"
            
            message_data = {
                "type": "message_edited",
                "chat_id": event.peer_id.user_id,
                "sender": display_name,
                "text": event.message.message or "",
                "message_id": event.message.id,
                "edited": True
            }
            
            logger.info(f"✏️ Message edited from {display_name}")
            await websocket_manager.broadcast_message(message_data)
            
        except Exception as e:
            logger.error(f"Error handling edited message: {e}")
    
    @client.on(events.MessageDeleted)
    async def handle_message_deleted(event):
        """Xử lý tin nhắn bị xóa"""
        try:
            message_data = {
                "type": "message_deleted",
                "message_ids": event.deleted_ids
            }
            
            logger.info(f"🗑️ Messages deleted: {event.deleted_ids}")
            await websocket_manager.broadcast_message(message_data)
            
        except Exception as e:
            logger.error(f"Error handling deleted message: {e}")
    
    @client.on(events.UserUpdate)
    async def handle_user_update(event):
        """Xử lý cập nhật trạng thái user (online/offline)"""
        try:
            # Chỉ log, không broadcast để tránh spam
            if hasattr(event, 'user_id'):
                logger.debug(f"👤 User {event.user_id} status updated")
                
        except Exception as e:
            logger.error(f"Error handling user update: {e}")
    
    logger.info("✅ All event handlers registered successfully")