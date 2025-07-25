# server/src/api/websocket.py
import json
import logging
from typing import List, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from telegram.schemas import WebSocketMessage

logger = logging.getLogger(__name__)
websocket_router = APIRouter()

class WebSocketManager:
    """Quản lý WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.connection_count = 0
    
    async def connect(self, websocket: WebSocket):
        """Chấp nhận WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        self.connection_count += 1
        
        logger.info(f"🔌 WebSocket connected. Total: {len(self.active_connections)}")
        
        # Gửi welcome message
        await self.send_personal_message(websocket, {
            "type": "connection",
            "message": "WebSocket connected successfully",
            "connection_id": self.connection_count
        })
    
    def disconnect(self, websocket: WebSocket):
        """Ngắt kết nối WebSocket"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"🔌 WebSocket disconnected. Total: {len(self.active_connections)}")
    
    async def send_personal_message(self, websocket: WebSocket, data: dict):
        """Gửi message tới một WebSocket cụ thể"""
        try:
            message = WebSocketMessage(type=data.get("type", "message"), data=data)
            await websocket.send_text(message.json())
        except Exception as e:
            logger.error(f"❌ Failed to send personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast_message(self, data: dict):
        """Broadcast message tới tất cả WebSocket connections"""
        if not self.active_connections:
            logger.debug("📡 No active WebSocket connections to broadcast to")
            return
        
        message = WebSocketMessage(
            type=data.get("type", "telegram_message"), 
            data=data
        )
        message_text = message.json()
        
        # Track failed connections để remove
        failed_connections = set()
        successful_broadcasts = 0
        
        for connection in self.active_connections.copy():  # Copy để tránh modify during iteration
            try:
                await connection.send_text(message_text)
                successful_broadcasts += 1
            except Exception as e:
                logger.warning(f"⚠️ Failed to broadcast to connection: {e}")
                failed_connections.add(connection)
        
        # Remove failed connections
        for failed_connection in failed_connections:
            self.disconnect(failed_connection)
        
        logger.info(f"📡 Broadcasted to {successful_broadcasts}/{len(self.active_connections) + len(failed_connections)} connections")
    
    async def send_status_update(self, status: str, details: dict = None):
        """Gửi status update tới tất cả clients"""
        await self.broadcast_message({
            "type": "status_update",
            "status": status,
            "details": details or {},
            "timestamp": None  # Sẽ được tự động thêm bởi WebSocketMessage
        })
    
    @property
    def connection_count_active(self) -> int:
        """Số lượng connections hiện tại"""
        return len(self.active_connections)

# Singleton instance
websocket_manager = WebSocketManager()

@websocket_router.websocket("")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint chính"""
    await websocket_manager.connect(websocket)
    
    try:
        while True:
            # Nhận message từ client (heartbeat, commands, etc.)
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                message_type = message_data.get("type", "unknown")
                
                logger.debug(f"📥 Received WebSocket message: {message_type}")
                
                # Handle different message types
                if message_type == "heartbeat":
                    await websocket_manager.send_personal_message(websocket, {
                        "type": "heartbeat_response",
                        "message": "pong",
                        "timestamp": None
                    })
                
                elif message_type == "get_status":
                    # Gửi trạng thái hiện tại
                    from telegram.client import telegram_manager
                    await websocket_manager.send_personal_message(websocket, {
                        "type": "status",
                        "telegram_connected": telegram_manager.is_connected,
                        "active_connections": websocket_manager.connection_count_active
                    })
                
                elif message_type == "echo":
                    # Echo message để test
                    await websocket_manager.send_personal_message(websocket, {
                        "type": "echo_response",
                        "original_message": message_data.get("message", ""),
                        "timestamp": None
                    })
                
                else:
                    logger.warning(f"⚠️ Unknown WebSocket message type: {message_type}")
                    await websocket_manager.send_personal_message(websocket, {
                        "type": "error",
                        "message": f"Unknown message type: {message_type}"
                    })
                    
            except json.JSONDecodeError:
                logger.warning(f"⚠️ Invalid JSON received: {data[:100]}...")
                await websocket_manager.send_personal_message(websocket, {
                    "type": "error",
                    "message": "Invalid JSON format"
                })
            
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
        logger.info("🔌 WebSocket disconnected normally")
        
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}", exc_info=True)
        websocket_manager.disconnect(websocket)