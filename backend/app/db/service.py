from typing import List, Optional
import uuid

from sqlalchemy import select, event
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import DbChat, DbMessage, DbTask, DbUserBase, DbMessagePart, DbArtifactPart, DbArtifact
from .schemas import ChatCreate, MessageCreate
from .database import get_user_engine, get_user_session

from a2a.types import Artifact, Message, Task, Role, Part
from loguru import logger

class UserDbService:
    """Service for database operations."""

    def __init__(self, session: AsyncSession, user_id: str):
        self.session = session
        self.user_id = user_id

    @classmethod
    async def ensure_user_db_initialized(cls, user_id: str):
        """Initialize database for a new user."""
        engine = get_user_engine(user_id)
        async with engine.begin() as conn:
            await conn.run_sync(DbUserBase.metadata.create_all)

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

    async def fetch_chat(self, chat_id: str) -> Optional[DbChat]:
        """Get a chat by ID."""
        query = (
            select(DbChat)
            .where(DbChat.id == chat_id, DbChat.user_id == self.user_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def fetch_chats(self) -> List[DbChat]:
        """List all chats for the current user."""
        query = (
            select(DbChat)
            .where(DbChat.user_id == self.user_id)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def delete_chat(self, chat_id: str) -> bool:
        """Delete a chat."""
        chat = await self.fetch_chat(chat_id)
        if chat and chat.user_id == self.user_id:
            await self.session.delete(chat)
            await self.session.commit()
            return True
        return False

    async def create_message_x(self, message_data: MessageCreate) -> DbMessage:
        """Create a new message."""
        # Verify the chat belongs to the current user
        chat = await self.fetch_chat(message_data.chat_id)
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
        chat = await self.fetch_chat(chat_id)
        if not chat or chat.user_id != self.user_id:
            return []

        query = select(DbMessage).where(DbMessage.chat_id == chat_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    
    def __build_message_content(self, message: Message) -> str:
        content = ""
        for part in message.parts:
            if part.root.kind == "text":
                content += part.root.text
        return content
    
    async def create_message(self, message: Message, chat_id: str, task_id: str, context_id: str | None = None) -> DbMessage:
        message = DbMessage(
            id=message.messageId,
            content=self.__build_message_content(message),
            chat_id=chat_id,
            role="assistant" if message.role == Role.agent else "user",
            task_id=task_id,
            context_id=context_id,
            _metadata=message.metadata,
            extensions=message.extensions,
        )
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)
        logger.info(f"Created message: {message}")
        return message
        
    async def fetch_message(self, message_id: str) -> Optional[DbMessage]:
        query = select(DbMessage).where(DbMessage.id == message_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def fetch_messages(self, chat_id: str, offset: int = 0, limit: int = 5) -> List[DbMessage]:
        query = select(DbMessage).where(DbMessage.chat_id == chat_id).offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def create_artifact(self, artifact: Artifact, task_id: str, context_id: str | None = None) -> DbArtifact:
        artifact = DbArtifact(
            id=artifact.artifactId,
            name=artifact.name,
            description=artifact.description,
            _metadata=artifact.metadata,
            extensions=artifact.extensions,
            task_id=task_id,
            context_id=context_id
        )
        self.session.add(artifact)
        await self.session.commit()
        await self.session.refresh(artifact)
        logger.info(f"Created artifact: {artifact}")
        return artifact
    
    async def fetch_artifact(self, artifact_id: str) -> Optional[DbArtifact]:
        query = select(DbArtifact).where(DbArtifact.id == artifact_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def fetch_artifacts(self, task_id: str) -> List[DbArtifact]:
        query = select(DbArtifact).where(DbArtifact.task_id == task_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def create_message_parts(self, message_id: str, parts: List[Part]) -> List[DbMessagePart]:
        message_parts = [DbMessagePart(
            id=str(uuid.uuid4()),
            message_id=message_id,
            part_type=part.root.kind,
            part_data=part.root.model_dump(exclude_none=True),
            _metadata=part.root.metadata if hasattr(part.root, "metadata") else None,
            part_index=index,
        ) for index, part in enumerate(parts)]
        self.session.add_all(message_parts)
        await self.session.commit()
        logger.info(f"Created message parts: {message_parts}")
        return message_parts
    
    async def fetch_message_parts(self, message_id: str) -> List[DbMessagePart]:
        query = select(DbMessagePart).where(DbMessagePart.message_id == message_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())    
    
    async def create_artifact_parts(self, artifact_id: str, parts: List[Part]) -> List[DbArtifactPart]:
        artifact_parts = [DbArtifactPart(
            id=str(uuid.uuid4()),
            artifact_id=artifact_id,
            part_type=part.root.kind,
            part_data=part.root.model_dump(exclude_none=True),
            _metadata=part.root.metadata if hasattr(part.root, "metadata") else None,
            part_index=index,
        ) for index, part in enumerate(parts)]
        self.session.add_all(artifact_parts)
        await self.session.commit()
        logger.info(f"Created artifact parts: {artifact_parts}")
        return artifact_parts

    async def fetch_artifact_parts(self, artifact_id: str) -> List[DbArtifactPart]:
        query = select(DbArtifactPart).where(DbArtifactPart.artifact_id == artifact_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())    
    
    
    async def create_task(self, task: Task, chat_id: str, agent_id: str) -> DbTask:
        task = DbTask(
            id=task.id,
            chat_id=chat_id,
            task_id=task.id,
            context_id=task.contextId,
            agent_id=agent_id,
            status=task.status.state.value,
            _metadata=task.metadata,
        )
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)
        logger.info(f"Created task: {task}")
        return task
    
    async def fetch_task(self, task_id: str) -> Optional[DbTask]:
        query = select(DbTask).where(DbTask.id == task_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def fetch_tasks(self, chat_id: str) -> List[DbTask]:
        query = select(DbTask).where(DbTask.chat_id == chat_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

