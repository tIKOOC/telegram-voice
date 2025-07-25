# server/src/telegram/schemas.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator

class TelegramMessage(BaseModel):
    """Model cho tin nhắn Telegram"""
    chat_id: int = Field(..., description="ID của chat/user")
    sender: str = Field(..., description="Tên người gửi")
    text: str = Field(..., description="Nội dung tin nhắn")
    message_id: Optional[int] = Field(None, description="ID của message")
    date: Optional[datetime] = Field(None, description="Thời gian gửi")
    type: str = Field(default="message", description="Loại message")
    
    @validator('text')
    def validate_text(cls, v):
        if not v or not v.strip():
            return ""
        return v.strip()
    
    @validator('sender')
    def validate_sender(cls, v):
        if not v or not v.strip():
            raise ValueError("Sender name cannot be empty")
        return v.strip()

class SendMessageRequest(BaseModel):
    """Request model cho gửi tin nhắn"""
    chat_id: int = Field(..., description="ID của chat để gửi tin")
    text: str = Field(..., min_length=1, max_length=4096, description="Nội dung tin nhắn")
    
    @validator('text')
    def validate_message_text(cls, v):
        if not v or not v.strip():
            raise ValueError("Message text cannot be empty")
        return v.strip()

class SendMessageResponse(BaseModel):
    """Response model cho việc gửi tin nhắn"""
    success: bool = Field(..., description="Trạng thái gửi tin")
    message: str = Field(..., description="Thông báo kết quả")
    message_id: Optional[int] = Field(None, description="ID của tin nhắn đã gửi")
    chat_id: Optional[int] = Field(None, description="ID của chat")
    timestamp: datetime = Field(default_factory=datetime.now, description="Thời gian xử lý")

class WebSocketMessage(BaseModel):
    """Model cho tin nhắn WebSocket"""
    type: str = Field(..., description="Loại message: message, error, status")
    data: dict = Field(default_factory=dict, description="Dữ liệu message")
    timestamp: datetime = Field(default_factory=datetime.now, description="Thời gian")

class TelegramUser(BaseModel):
    """Model cho thông tin user Telegram"""
    id: int = Field(..., description="User ID")
    username: Optional[str] = Field(None, description="Username")
    first_name: Optional[str] = Field(None, description="Họ")
    last_name: Optional[str] = Field(None, description="Tên")
    phone: Optional[str] = Field(None, description="Số điện thoại")
    
    @property
    def display_name(self) -> str:
        """Tên hiển thị của user"""
        names = []
        if self.first_name:
            names.append(self.first_name)
        if self.last_name:
            names.append(self.last_name)
        
        if names:
            return " ".join(names)
        elif self.username:
            return f"@{self.username}"
        else:
            return f"User{self.id}"

class ChatInfo(BaseModel):
    """Thông tin chat"""
    id: int = Field(..., description="Chat ID")
    type: str = Field(..., description="Loại chat: private, group, channel")
    title: Optional[str] = Field(None, description="Tiêu đề chat")
    username: Optional[str] = Field(None, description="Username của chat")
    member_count: Optional[int] = Field(None, description="Số thành viên")

class ErrorResponse(BaseModel):
    """Model cho error response"""
    error: bool = Field(default=True)
    message: str = Field(..., description="Thông báo lỗi")
    error_type: Optional[str] = Field(None, description="Loại lỗi")
    details: Optional[dict] = Field(None, description="Chi tiết lỗi")
    timestamp: datetime = Field(default_factory=datetime.now)