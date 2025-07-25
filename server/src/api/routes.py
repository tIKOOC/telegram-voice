# server/src/api/routes.py
import logging
from fastapi import APIRouter, HTTPException, Depends
from telegram.client import telegram_manager
from telegram.schemas import (
    SendMessageRequest, 
    SendMessageResponse, 
    ErrorResponse,
    TelegramUser,
    ChatInfo
)
from core.config import settings

logger = logging.getLogger(__name__)
api_router = APIRouter()

async def get_telegram_client():
    """Dependency để lấy Telegram client"""
    if not telegram_manager.is_connected:
        raise HTTPException(
            status_code=503, 
            detail="Telegram client not connected"
        )
    return telegram_manager.client

@api_router.post("/send", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
    client = Depends(get_telegram_client)
):
    """Gửi tin nhắn tới chat/user"""
    try:
        logger.info(f"📤 Sending message to chat {request.chat_id}: {request.text[:50]}...")
        
        # Gửi tin nhắn qua Telegram
        sent_message = await telegram_manager.send_message_safe(
            chat_id=request.chat_id,
            message=request.text
        )
        
        logger.info(f"✅ Message sent successfully. ID: {sent_message.id}")
        
        return SendMessageResponse(
            success=True,
            message="Message sent successfully",
            message_id=sent_message.id,
            chat_id=request.chat_id
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to send message: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send message: {str(e)}"
        )

@api_router.get("/me", response_model=TelegramUser)
async def get_me(client = Depends(get_telegram_client)):
    """Lấy thông tin user hiện tại"""
    try:
        me = await client.get_me()
        return TelegramUser(
            id=me.id,
            username=me.username,
            first_name=me.first_name,
            last_name=me.last_name,
            phone=me.phone
        )
    except Exception as e:
        logger.error(f"❌ Failed to get user info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get user info: {str(e)}"
        )

@api_router.get("/chats")
async def get_recent_chats(client = Depends(get_telegram_client), limit: int = 20):
    """Lấy danh sách chat gần đây"""
    try:
        dialogs = []
        async for dialog in client.iter_dialogs(limit=limit):
            chat_info = {
                "id": dialog.id,
                "title": dialog.title or dialog.name,
                "type": "private" if dialog.is_user else ("group" if dialog.is_group else "channel"),
                "unread_count": dialog.unread_count,
                "last_message_date": dialog.date.isoformat() if dialog.date else None
            }
            
            # Thêm thông tin user nếu là chat riêng
            if dialog.is_user:
                entity = await client.get_entity(dialog.id)
                chat_info.update({
                    "username": getattr(entity, 'username', None),
                    "first_name": getattr(entity, 'first_name', None),
                    "last_name": getattr(entity, 'last_name', None)
                })
            
            dialogs.append(chat_info)
        
        return {"chats": dialogs, "total": len(dialogs)}
        
    except Exception as e:
        logger.error(f"❌ Failed to get chats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get chats: {str(e)}"
        )

@api_router.get("/chat/{chat_id}/messages")
async def get_chat_messages(
    chat_id: int, 
    client = Depends(get_telegram_client),
    limit: int = 50
):
    """Lấy tin nhắn từ chat"""
    try:
        messages = []
        async for message in client.iter_messages(chat_id, limit=limit):
            sender_name = "Unknown"
            if message.sender:
                if hasattr(message.sender, 'first_name'):
                    sender_name = f"{message.sender.first_name or ''} {message.sender.last_name or ''}".strip()
                    if not sender_name:
                        sender_name = message.sender.username or f"User{message.sender.id}"
                
            messages.append({
                "id": message.id,
                "text": message.text or "",
                "sender": sender_name,
                "date": message.date.isoformat() if message.date else None,
                "out": message.out,
                "media": message.media is not None
            })
        
        return {"messages": messages, "chat_id": chat_id, "total": len(messages)}
        
    except Exception as e:
        logger.error(f"❌ Failed to get messages from chat {chat_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get messages: {str(e)}"
        )

@api_router.get("/status")
async def get_status():
    """Lấy trạng thái hệ thống"""
    return {
        "telegram": {
            "connected": telegram_manager.is_connected,
            "client_ready": telegram_manager.client is not None
        },
        "websocket": {
            "active_connections": len(getattr(telegram_manager, '_websocket_connections', []))
        },
        "config": {
            "debug": settings.debug,
            "app_name": settings.app_name
        }
    }

@api_router.post("/test")
async def test_connection(client = Depends(get_telegram_client)):
    """Test kết nối Telegram"""
    try:
        me = await client.get_me()
        dialogs_count = 0
        async for _ in client.iter_dialogs(limit=10):
            dialogs_count += 1
        
        return {
            "success": True,
            "message": "Telegram connection is working",
            "user": {
                "id": me.id,
                "name": f"{me.first_name or ''} {me.last_name or ''}".strip(),
                "username": me.username
            },
            "dialogs_accessible": dialogs_count
        }
        
    except Exception as e:
        logger.error(f"❌ Connection test failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Connection test failed: {str(e)}"
        )