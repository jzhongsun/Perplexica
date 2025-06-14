from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import ChatCreate, ChatResponse, MessageCreate, MessageResponse
from .service import DatabaseService
from .database import get_session

router = APIRouter(prefix="/db", tags=["database"])

@router.post("/chats", response_model=ChatResponse)
async def create_chat(
    chat_data: ChatCreate,
    session: AsyncSession = Depends(get_session)
) -> ChatResponse:
    """Create a new chat."""
    db_service = DatabaseService(session)
    chat = await db_service.create_chat(chat_data)
    return ChatResponse.model_validate(chat)

@router.get("/chats/{chat_id}", response_model=ChatResponse)
async def get_chat(
    chat_id: str,
    session: AsyncSession = Depends(get_session)
) -> ChatResponse:
    """Get a chat by ID."""
    db_service = DatabaseService(session)
    chat = await db_service.get_chat(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return ChatResponse.model_validate(chat)

@router.get("/chats", response_model=List[ChatResponse])
async def list_chats(
    session: AsyncSession = Depends(get_session)
) -> List[ChatResponse]:
    """List all chats."""
    db_service = DatabaseService(session)
    chats = await db_service.list_chats()
    return [ChatResponse.model_validate(chat) for chat in chats]

@router.delete("/chats/{chat_id}")
async def delete_chat(
    chat_id: str,
    session: AsyncSession = Depends(get_session)
) -> dict:
    """Delete a chat."""
    db_service = DatabaseService(session)
    success = await db_service.delete_chat(chat_id)
    if not success:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"status": "success", "message": "Chat deleted"}

@router.post("/messages", response_model=MessageResponse)
async def create_message(
    message_data: MessageCreate,
    session: AsyncSession = Depends(get_session)
) -> MessageResponse:
    """Create a new message."""
    db_service = DatabaseService(session)
    message = await db_service.create_message(message_data)
    return MessageResponse.model_validate(message)

@router.get("/chats/{chat_id}/messages", response_model=List[MessageResponse])
async def get_chat_messages(
    chat_id: str,
    session: AsyncSession = Depends(get_session)
) -> List[MessageResponse]:
    """Get all messages for a chat."""
    db_service = DatabaseService(session)
    messages = await db_service.get_chat_messages(chat_id)
    return [MessageResponse.model_validate(message) for message in messages] 