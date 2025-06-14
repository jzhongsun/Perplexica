from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import Chat, Message
from .schemas import ChatCreate, MessageCreate

class DatabaseService:
    """Service for database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_chat(self, chat_data: ChatCreate) -> Chat:
        """Create a new chat."""
        chat = Chat(
            id=chat_data.id,
            title=chat_data.title,
            focus_mode=chat_data.focus_mode,
            files=[file.model_dump() for file in chat_data.files]
        )
        self.session.add(chat)
        await self.session.commit()
        await self.session.refresh(chat)
        return chat

    async def get_chat(self, chat_id: str) -> Optional[Chat]:
        """Get a chat by ID."""
        query = select(Chat).options(selectinload(Chat.messages)).where(Chat.id == chat_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_chats(self) -> List[Chat]:
        """List all chats."""
        query = select(Chat).options(selectinload(Chat.messages))
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def delete_chat(self, chat_id: str) -> bool:
        """Delete a chat."""
        chat = await self.get_chat(chat_id)
        if chat:
            await self.session.delete(chat)
            await self.session.commit()
            return True
        return False

    async def create_message(self, message_data: MessageCreate) -> Message:
        """Create a new message."""
        message = Message(
            content=message_data.content,
            chat_id=message_data.chat_id,
            message_id=message_data.message_id,
            role=message_data.role,
            extra_info=message_data.extra_info
        )
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)
        return message

    async def get_chat_messages(self, chat_id: str) -> List[Message]:
        """Get all messages for a chat."""
        query = select(Message).where(Message.chat_id == chat_id)
        result = await self.session.execute(query)
        return list(result.scalars().all()) 