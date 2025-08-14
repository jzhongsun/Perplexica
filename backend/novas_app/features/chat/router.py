"""Chat router module."""
from fastapi import APIRouter, Depends
from typing import List

from .service import ChatService
from .schemas import (
    ChatListResponse,
    ChatHistory,
    ChatMetadata,
    ChatRequest,
    MessagesResponse,
    ChatResponse
)
from novas_app.depends import get_chat_service
from novas_app.core.ui_messages import UIMessage

router = APIRouter(prefix="/chats", tags=["chat"])
@router.get("", response_model=ChatListResponse)
async def list_chats(
    chat_service: ChatService = Depends(get_chat_service)
) -> ChatListResponse:
    """List all chats."""
    response = await chat_service.list_chats()
    return ChatListResponse(chats=response, status=200)

@router.post("", response_model=ChatHistory)
async def create_chat(
    chatRequest: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
) -> ChatHistory:
    """Get chat metadata by ID."""
    return await chat_service.create_chat(chatRequest)


@router.get("/{chat_id}", response_model=ChatHistory)
async def get_chat(
    chat_id: str,
    chat_service: ChatService = Depends(get_chat_service)
) -> ChatHistory:
    """Get chat history by ID."""
    return await chat_service.get_chat(chat_id)

@router.delete("/{chat_id}")
async def delete_chat(
    chat_id: str,
    chat_service: ChatService = Depends(get_chat_service)
) -> dict:
    """Delete chat by ID."""
    await chat_service.delete_chat(chat_id)
    return {"status": "success", "message": "Chat deleted"} 


@router.get("/{chat_id}/messages", response_model=MessagesResponse)
async def get_chat_messages(
    chat_id: str,
    offset: int = 0,
    limit: int = 100,
    chat_service: ChatService = Depends(get_chat_service)
) -> MessagesResponse:
    """Get chat messages by ID."""
    return await chat_service.fetch_messages_of_chat(chat_id, offset, limit)