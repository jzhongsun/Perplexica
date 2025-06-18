from typing import List, Optional, Dict, Any, Literal, Type
from pydantic import BaseModel, Field, model_validator
from datetime import datetime, timezone
from app.core.ui_messages import (
    UIMessage,
    UIMessagePart,
    TextUIPart,
    ReasoningUIPart,
    SourceUrlUIPart,
    SourceDocumentUIPart,
    FileUIPart,
    DataUIPart,
    StepStartUIPart,
    ToolUIPart
)

def create_message_part(data: Dict[str, Any]) -> UIMessagePart:
    """Factory function to create appropriate UIMessagePart based on type."""
    part_type = data.get('type')
    if not part_type:
        raise ValueError("Message part must have a type")

    if part_type == 'text':
        return TextUIPart(type='text', text=data['text'])
    elif part_type == 'reasoning':
        return ReasoningUIPart(
            type='reasoning',
            text=data['text'],
            providerMetadata=data.get('providerMetadata')
        )
    elif part_type == 'source-url':
        return SourceUrlUIPart(
            type='source-url',
            sourceId=data['sourceId'],
            url=data['url'],
            title=data.get('title'),
            providerMetadata=data.get('providerMetadata')
        )
    elif part_type == 'source-document':
        return SourceDocumentUIPart(
            type='source-document',
            sourceId=data['sourceId'],
            mediaType=data['mediaType'],
            title=data['title'],
            filename=data.get('filename'),
            providerMetadata=data.get('providerMetadata')
        )
    elif part_type == 'file':
        return FileUIPart(
            type='file',
            mediaType=data['mediaType'],
            filename=data.get('filename'),
            url=data['url']
        )
    elif part_type == 'step-start':
        return StepStartUIPart(type='step-start')
    elif part_type.startswith('data-'):
        return DataUIPart(
            type=part_type,
            id=data.get('id'),
            data=data['data']
        )
    elif part_type.startswith('tool-'):
        # Handle tool parts based on state
        tool_base = {
            'type': part_type,
            'toolCallId': data['toolCallId'],
            'args': data.get('args', {})
        }
        if data.get('result') is not None:
            return ToolUIPart(state='result', result=data['result'], **tool_base)
        elif data.get('state') == 'partial-call':
            return ToolUIPart(state='partial-call', **tool_base)
        else:
            return ToolUIPart(state='call', **tool_base)
    else:
        raise ValueError(f"Unknown message part type: {part_type}")

class Message(BaseModel):
    """Message model."""
    chat_id: str
    message_id: str
    role: Literal['user', 'assistant'] = Field(..., description="Role of the message sender (system/user/assistant)")
    content: str = Field(..., description="Content of the message")
    timestamp: datetime = Field(default=datetime.now(timezone.utc))

class ChatModel(BaseModel):
    provider: str = Field(..., description="Model provider")
    name: str = Field(..., description="Model name")
    customOpenAIKey: Optional[str] = None
    customOpenAIBaseURL: Optional[str] = None

class EmbeddingModel(BaseModel):
    provider: str = Field(..., description="Model provider")
    name: str = Field(..., description="Model name")

# enum OptimizationMode

class ChatRequestOptions(BaseModel):
    optimization_mode: Optional[Literal['speed', 'balanced', 'quality']] = Field(default=None, description="Optimization mode")
    focus_mode: Optional[str] = Field(default=None, description="Focus mode")
    system_instructions: Optional[str] = Field(default=None, description="System instructions")

class ChatRequest(BaseModel):
    """Chat request model."""
    chat_id: Optional[str] = Field(None, description="Chat ID for continuing conversation")
    messages: List[UIMessage] = Field(..., description="List of messages")
    options: Optional[Dict[str, Any]] = Field(default=None)

    @model_validator(mode='before')
    @classmethod
    def validate_messages(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process messages using the factory function."""
        if not isinstance(data, dict):
            return data
            
        messages = data.get('messages', [])
        if not isinstance(messages, list):
            return data
            
        for msg in messages:
            if isinstance(msg, dict) and 'parts' in msg:
                msg['parts'] = [
                    create_message_part(part) if isinstance(part, dict) else part
                    for part in msg['parts']
                ]
        
        return data

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