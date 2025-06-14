from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime

class Message(BaseModel):
    """Message model."""
    role: str = Field(..., description="Role of the message sender (user/assistant)")
    content: str = Field(..., description="Content of the message")
    timestamp: datetime = Field(default_factory=datetime.now)

class ChatModel(BaseModel):
    provider: str = Field(..., description="Model provider")
    name: str = Field(..., description="Model name")
    customOpenAIKey: Optional[str] = None
    customOpenAIBaseURL: Optional[str] = None

class EmbeddingModel(BaseModel):
    provider: str = Field(..., description="Model provider")
    name: str = Field(..., description="Model name")

class ChatRequest(BaseModel):
    """Chat request model."""
    message: str = Field(..., description="Message content")
    chat_id: Optional[str] = Field(None, description="Chat ID for continuing conversation")
    stream: bool = Field(default=True, description="Whether to stream the response")

class ChatResponse(BaseModel):
    """Chat response model."""
    chat_id: str = Field(..., description="Unique chat identifier")
    message: Message = Field(..., description="Response message")

class ChatMetadata(BaseModel):
    """Chat metadata model."""
    chat_id: str = Field(..., description="Unique chat identifier")
    title: str = Field(..., description="Chat title")
    created_at: datetime = Field(..., description="Chat creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

class ChatHistory(BaseModel):
    """Chat history model."""
    chat_id: str = Field(..., description="Unique chat identifier")
    messages: List[Message] = Field(default_factory=list, description="List of messages")
    metadata: ChatMetadata = Field(..., description="Chat metadata")

class StreamResponse(BaseModel):
    type: Literal["message", "sources", "messageEnd", "error"] = Field(..., description="Response type")
    data: Optional[str] = None
    messageId: Optional[str] = None
    sources: Optional[List[Dict[str, Any]]] = None

class NonStreamResponse(BaseModel):
    message: str = Field(..., description="Complete response message")
    sources: Optional[List[Dict[str, Any]]] = Field(default=None)

class MessageMetadata(BaseModel):
    createdAt: datetime = Field(default_factory=datetime.now)
    sources: Optional[List[Dict[str, Any]]] = None 
    
class ChatListResponse(BaseModel):
    chats: List[ChatMetadata] = Field(..., description="List of chats")
    status: int = Field(..., description="Status of the response")