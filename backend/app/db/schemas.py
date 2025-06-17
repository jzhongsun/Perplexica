from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class FileInfo(BaseModel):
    """File information schema."""
    name: str
    file_id: str = Field(..., alias="fileId")

    class Config:
        populate_by_name = True

class MessageBase(BaseModel):
    """Base message schema."""
    content: str
    role: str
    extra_info: Optional[dict] = None

class MessageCreate(MessageBase):
    """Schema for creating a new message."""
    chat_id: str = Field(..., alias="chatId")
    message_id: str = Field(..., alias="messageId")

    class Config:
        populate_by_name = True

class MessageResponse(MessageBase):
    """Schema for message response."""
    id: int
    chat_id: str = Field(..., alias="chatId")
    message_id: str = Field(..., alias="messageId")

    class Config:
        from_attributes = True
        populate_by_name = True

class ChatBase(BaseModel):
    """Base chat schema."""
    title: str
    focus_mode: str = Field(..., alias="focusMode")
    files: List[FileInfo] = []

    class Config:
        populate_by_name = True

class ChatCreate(ChatBase):
    """Schema for creating a new chat."""
    id: str
    user_id: str = Field(..., alias="userId")

class ChatResponse(ChatBase):
    """Schema for chat response."""
    id: str
    user_id: str = Field(..., alias="userId")
    created_at: datetime = Field(..., alias="createdAt")
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True
        populate_by_name = True 