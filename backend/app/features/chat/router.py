"""Chat router module."""
from fastapi import APIRouter, Depends

from .service import ChatService
from .schemas import (
    ChatListResponse,
    ChatHistory
)

router = APIRouter(prefix="/chats", tags=["chat"])
@router.get("", response_model=ChatListResponse)
async def list_chats(
    chat_service: ChatService = Depends(ChatService)
) -> ChatListResponse:
    """List all chats."""
    response = await chat_service.list_chats()
    return ChatListResponse(chats=response, status=200)

@router.get("/{chat_id}", response_model=ChatHistory)
async def get_chat(
    chat_id: str,
    chat_service: ChatService = Depends(ChatService)
) -> ChatHistory:
    """Get chat history by ID."""
    return await chat_service.get_chat(chat_id)

@router.delete("/{chat_id}")
async def delete_chat(
    chat_id: str,
    chat_service: ChatService = Depends(ChatService)
) -> dict:
    """Delete chat by ID."""
    await chat_service.delete_chat(chat_id)
    return {"status": "success", "message": "Chat deleted"} 