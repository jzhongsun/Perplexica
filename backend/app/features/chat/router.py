"""Chat router module."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from .service import ChatService
from .schemas import (
    ChatListResponse,
    ChatRequest,
    ChatResponse,
    Message,
    ChatHistory,
    ChatMetadata
)

router = APIRouter(prefix="", tags=["chat"])

@router.post("/chat", response_model=ChatResponse)
async def create_chat(
    request: ChatRequest,
    chat_service: ChatService = Depends(ChatService)
) -> ChatResponse:
    """Create a new chat."""
    print(request)
    return await chat_service.create_chat(request)

@router.get("/chats", response_model=ChatListResponse)
async def list_chats(
    chat_service: ChatService = Depends(ChatService)
) -> ChatListResponse:
    """List all chats."""
    response = await chat_service.list_chats()
    return ChatListResponse(chats=response, status=200)

@router.get("/chats/{chat_id}", response_model=ChatHistory)
async def get_chat(
    chat_id: str,
    chat_service: ChatService = Depends(ChatService)
) -> ChatHistory:
    """Get chat history by ID."""
    return await chat_service.get_chat(chat_id)

@router.delete("/chats/{chat_id}")
async def delete_chat(
    chat_id: str,
    chat_service: ChatService = Depends(ChatService)
) -> dict:
    """Delete chat by ID."""
    await chat_service.delete_chat(chat_id)
    return {"status": "success", "message": "Chat deleted"} 