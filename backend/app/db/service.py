from typing import List, Optional
from sqlalchemy import select, event
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import DbChat, DbMessage, DbBase
from .schemas import ChatCreate, MessageCreate
from .database import get_user_engine, get_user_session


class DatabaseService:
    """Service for database operations."""

    def __init__(self, session: AsyncSession, user_id: str):
        self.session = session
        self.user_id = user_id

    @classmethod
    async def initialize_user_database(cls, user_id: str):
        """Initialize database for a new user."""
        engine = get_user_engine(user_id)
        async with engine.begin() as conn:
            await conn.run_sync(DbBase.metadata.create_all)

    async def create_chat(self, chat_data: ChatCreate) -> DbChat:
        """Create a new chat."""
        chat = DbChat(
            id=chat_data.id,
            title=chat_data.title,
            focus_mode=chat_data.focus_mode,
            files=[file.model_dump() for file in chat_data.files],
            user_id=self.user_id,  # Add user_id to chat
        )
        self.session.add(chat)
        await self.session.commit()
        await self.session.refresh(chat)
        return chat

    async def get_chat(self, chat_id: str) -> Optional[DbChat]:
        """Get a chat by ID."""
        query = (
            select(DbChat)
            .options(selectinload(DbChat.messages))
            .where(DbChat.id == chat_id, DbChat.user_id == self.user_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_chats(self) -> List[DbChat]:
        """List all chats for the current user."""
        query = (
            select(DbChat)
            .options(selectinload(DbChat.messages))
            .where(DbChat.user_id == self.user_id)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def delete_chat(self, chat_id: str) -> bool:
        """Delete a chat."""
        chat = await self.get_chat(chat_id)
        if chat and chat.user_id == self.user_id:
            await self.session.delete(chat)
            await self.session.commit()
            return True
        return False

    async def create_message(self, message_data: MessageCreate) -> DbMessage:
        """Create a new message."""
        # Verify the chat belongs to the current user
        chat = await self.get_chat(message_data.chat_id)
        if not chat or chat.user_id != self.user_id:
            raise ValueError("Chat not found or access denied")

        message = DbMessage(
            content=message_data.content,
            chat_id=message_data.chat_id,
            message_id=message_data.message_id,
            role=message_data.role,
            extra_info=message_data.extra_info,
        )
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)
        return message

    async def get_chat_messages(self, chat_id: str) -> List[DbMessage]:
        """Get all messages for a chat."""
        # Verify the chat belongs to the current user
        chat = await self.get_chat(chat_id)
        if not chat or chat.user_id != self.user_id:
            return []

        query = select(DbMessage).where(DbMessage.chat_id == chat_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())
